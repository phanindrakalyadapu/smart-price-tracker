from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.user import User
from app.models.wishlist import Wishlist
from app.services.email_utils import send_price_change_email
import asyncio

scheduler = BackgroundScheduler()

def _get_new_price_sync(url: str, site: str):
    """
    Your scrapers are async; run them safely in this background thread using asyncio.
    """
    from app.services.pure_ai_scraper import PureAIScraper
    async def _run():
        scraper = PureAIScraper()
        if site == "amazon" or ("amazon.com" in url and site == "auto"):
            return await scraper.amazon_scraper(url)
        return await scraper.generic_scraper(url)

    return asyncio.run(_run())

def check_all_prices():
    db: Session = SessionLocal()
    try:
        products = db.query(Product).all()
        for p in products:
            try:
                scraped = _get_new_price_sync(p.url, p.site)
                if not scraped or scraped.get("price") is None:
                    continue
                new_price = scraped["price"]

                last = (
                    db.query(PriceHistory)
                    .filter(PriceHistory.product_id == p.id)
                    .order_by(PriceHistory.fetched_at.desc())
                    .first()
                )

                # 1) first ever record for this product -> creates baseline entry, no email
                if not last:
                    baseline_note = "Tracking started. AI will analyze once the price updates."
                    db.add(PriceHistory(product_id=p.id, price=new_price, ai_summary=baseline_note))
                    db.commit()
                    continue  # nothing else to do for first insert

                #2) No changes -> do nothing 
                if last.price == new_price:
                    continue  
                # 3) Price changed -> store new price, generate AI insight, notify users
                old_price = last.price

                #Prefer real description if your scraper returns it
                scrapped_desc = scraped.get("description") or p.color or p.site
                
                from app.services.ai_analysis import analyze_product_with_gpt
                ai_insight, review_summary = asyncio.run(analyze_product_with_gpt(p.name, old_price, new_price, description=scrapped_desc))

                # 🧠 Store AI insight with price history
                db.add(PriceHistory(product_id=p.id, price=new_price, ai_summary=ai_insight))
                db.commit()

                # Notify all users who track this product
                followers = db.query(Wishlist).filter(Wishlist.product_id == p.id).all()
                
                for w in followers:
                    u = db.execute(select(User).where(User.id == w.user_id)).scalar_one_or_none()
                    if not u:
                        continue
                    asyncio.run(
                        send_price_change_email(
                            to_email=u.email,
                            first_name=u.first_name,
                            product_name=p.name,
                            product_url=p.url,
                            old_price=old_price if old_price is not None else new_price,
                            new_price=new_price,
                            #description=p.color or p.site,
                            ai_summary=ai_insight,
                            review_summary=review_summary,
                            )    
                        )
            except Exception as e:
                db.rollback()
                print(f"❌ Error checking product {p.id}: {e}")
    finally:
        db.close()

def start_scheduler():
    # every 10 minutes
    scheduler.add_job(check_all_prices, "interval", minutes=15, id="price_watch_job", replace_existing=True)
    scheduler.start()

def shutdown_scheduler():
    scheduler.shutdown(wait=False)
