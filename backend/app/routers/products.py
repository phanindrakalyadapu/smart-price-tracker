from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import SessionLocal, get_db
from app.models.product import Product
from app.models.wishlist import Wishlist
from app.schemas.product import ProductCreate, ProductResponse, ProductIngestRequest
from app.models.price_history import PriceHistory
from app.services.scraper import scrape_product
# ✅ Send confirmation email to the user
from app.services.email_utils import send_product_added_email
from app.models.user import User
from app.models.wishlist import Wishlist
import json
import asyncio
from urllib.parse import urlparse

router = APIRouter(prefix="/products", tags=["Products"])

# Dependency: create a new DB session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create Product
@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(
        name=product.name,
        url=product.url,
        site=product.site,
        image_url=product.image_url
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return ProductResponse.model_validate(db_product)

# Get All Products
@router.get("/", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [ProductResponse.model_validate(product) for product in products]

# Get Product by ID
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)

# Delete Product
@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.post("/ingest", response_model=ProductResponse, status_code=201)
async def ingest_product(body: ProductIngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Ingest a product URL, scrape details, create Product if needed,
    attach to user's wishlist, and save initial price to PriceHistory.
    """
    print("🎯 Starting product ingestion...")

    try:
        from app.services.pure_ai_scraper import PureAIScraper
        scraper = PureAIScraper()

        # Step 1 – Check existing product
        existing = db.execute(select(Product).where(Product.url == str(body.url))).scalar_one_or_none()

        # Step 2 – Scrape product info
        if body.site == "amazon" or ("amazon.com" in str(body.url) and body.site == "auto"):
            scraped = await scraper.amazon_scraper(str(body.url))
            scraper_used = "amazon_scraper"
        else:
            scraped = await scraper.generic_scraper(str(body.url))
            scraper_used = "generic_scraper"

        print(f"📦 Used {scraper_used}, scraped:", scraped)

        if not scraped or not scraped.get("name"):
            raise HTTPException(status_code=400, detail="Failed to scrape product data")

        # Step 3 – Create or reuse product
        if existing:
            product = existing
        else:
            product = Product(
                name=scraped.get("name", "Unknown Product"),
                url=str(body.url),
                site=body.site,
                image_url=scraped.get("image_url"),
                color=scraped.get("color"),
                specs_json=json.dumps(scraped.get("specs", {})),
            )
            db.add(product)
            db.flush()  # so we get product.id

        # Step 4 – Link user→product in wishlist
        if body.user_id:
            wl = (
                db.query(Wishlist)
                .filter(Wishlist.user_id == body.user_id, Wishlist.product_id == product.id)
                .first()
            )
            if not wl:
                db.add(Wishlist(user_id=body.user_id, product_id=product.id))

        # Step 5 – Save initial price history if missing or changed
        if scraped.get("price") is not None:
            last = (
                db.query(PriceHistory)
                .filter(PriceHistory.product_id == product.id)
                .order_by(PriceHistory.fetched_at.desc())
                .first()
            )
            if not last:
                baseline_note = "Tracking started. AI will analyze once the price updates."
                db.add(PriceHistory(product_id=product.id, price=scraped["price"], ai_summary=baseline_note))
            elif last.price != scraped["price"]:
                db.add(PriceHistory(product_id=product.id, price=scraped["price"]))
        db.commit()
        db.refresh(product)
        print(f"✅ Product saved successfully (used {scraper_used})")

        wl = (
            db.query(Wishlist)
            .filter(Wishlist.product_id == product.id, Wishlist.user_id == body.user_id)
            .first()
        )
        if wl:
            user = db.query(User).filter(User.id == wl.user_id).first()
            if user and scraped.get("price") is not None:
                background_tasks.add_task(
                    send_product_added_email,
                    user.email,
                    user.first_name,
                    product.name,
                    product.url,
                    float(scraped.get("price", 0.0))
                )

        return ProductResponse.model_validate(product)

    except Exception as e:
        db.rollback()
        import traceback
        print(f"❌ ingest_product error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
