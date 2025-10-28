from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.wishlist import Wishlist
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.schemas.wishlist import WishlistItemResponse
from app.models.user import User
from datetime import datetime

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])

# Add product to wishlist
@router.post("/")
def add_to_wishlist(user_id: int, product_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not user or not product:
        raise HTTPException(status_code=404, detail="User or Product not found")
    
    wishlist_item = Wishlist(user_id=user_id, product_id=product_id, created_at=datetime.utcnow())
    db.add(wishlist_item)
    db.commit()
    db.refresh(wishlist_item)
    return wishlist_item

# Get all wishlist items
@router.get("/")
def get_all_wishlist(db: Session = Depends(get_db)):
    return db.query(Wishlist).all()

# Get wishlist by user
@router.get("/{user_id}", response_model=list[WishlistItemResponse])
def get_user_wishlist(user_id: int, db: Session = Depends(get_db)):
    """
    Returns all products in a user's wishlist with their latest price and link.
    """
    # Fetch all wishlist entries for this user
    wishlist_entries = db.query(Wishlist).filter(Wishlist.user_id == user_id).all()
    if not wishlist_entries:
        raise HTTPException(status_code=404, detail="No products found in wishlist")

    results = []
    for entry in wishlist_entries:
        product = db.query(Product).filter(Product.id == entry.product_id).first()
        if not product:
            continue

        # Get the latest price from PriceHistory
        latest_price_entry = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == product.id)
            .order_by(PriceHistory.fetched_at.desc())
            .first()
        )

        results.append({
            "product_id": product.id,
            "name": product.name,
            "url": product.url,
            "site": product.site,
            "image_url": product.image_url,
            "current_price": latest_price_entry.price if latest_price_entry else None,
            "last_updated": str(latest_price_entry.fetched_at) if latest_price_entry else None,
        })

    return results

# Delete wishlist item
@router.delete("/user/{user_id}/product/{product_id}")
def delete_product_from_wishlist(user_id: int, product_id: int, db: Session = Depends(get_db)):
    """
    Delete a product from a user's wishlist and remove all related records:
    - Wishlist entry
    - Product record
    - Price history entries
    """
    try:
        # 1️⃣ Confirm wishlist entry exists
        wishlist_item = (
            db.query(Wishlist)
            .filter(Wishlist.user_id == user_id, Wishlist.product_id == product_id)
            .first()
        )
        if not wishlist_item:
            raise HTTPException(status_code=404, detail="Wishlist item not found")

        # 2️⃣ Delete related price history
        db.query(PriceHistory).filter(PriceHistory.product_id == product_id).delete(synchronize_session=False)

        # 4️⃣ Delete wishlist record
        db.query(Wishlist).filter(Wishlist.user_id == user_id, Wishlist.product_id == product_id).delete(synchronize_session=False)

        # 3️⃣ Delete product record
        db.query(Product).filter(Product.id == product_id).delete(synchronize_session=False)

        db.commit()
        print(f"✅ Deleted product {product_id} and all related records for user {user_id}")
        return {"message": "Product and all related records deleted successfully"}

    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")