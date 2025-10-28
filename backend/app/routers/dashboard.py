from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.wishlist import Wishlist
from app.models.product import Product
from app.models.price_history import PriceHistory

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/{user_id}")
def get_user_dashboard(user_id: int, db: Session = Depends(get_db)):
    # Verify user exists
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wishlist_items = (
        db.query(Wishlist)
        .filter(Wishlist.user_id == user_id)
        .all()
    )

    dashboard_data = []
    for item in wishlist_items:
        product = db.get(Product, item.product_id)
        if not product:
            continue

        # Get latest price history
        last_history = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == product.id)
            .order_by(PriceHistory.fetched_at.desc())
            .first()
        )

        if last_history:
            dashboard_data.append({
                "product_id": product.id,
                "product_name": product.name,
                "url": product.url,
                "image_url": product.image_url,
                "current_price": last_history.price,
                "ai_summary": last_history.ai_summary,
            })

    return dashboard_data
