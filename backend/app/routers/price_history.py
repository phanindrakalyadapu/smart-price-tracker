from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.price_history import PriceHistory
from app.models.product import Product
from app.schemas.price_history import PriceHistoryCreate, PriceHistoryResponse

router = APIRouter(prefix="/price-history", tags=["Price History"])

# ✅ Add a new price record
@router.post("/", response_model=PriceHistoryResponse, status_code=201)
def add_price_record(data: PriceHistoryCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_record = PriceHistory(product_id=data.product_id, price=data.price)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


# ✅ Get all price records for a product
@router.get("/{product_id}", response_model=list[PriceHistoryResponse])
def get_price_history(product_id: int, db: Session = Depends(get_db)):
    records = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.fetched_at.desc()).all()
    if not records:
        raise HTTPException(status_code=404, detail="No price history found for this product")
    return records
