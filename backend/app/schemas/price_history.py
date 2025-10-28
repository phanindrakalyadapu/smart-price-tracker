from datetime import datetime
from pydantic import BaseModel

class PriceHistoryBase(BaseModel):
    price: float

class PriceHistoryCreate(PriceHistoryBase):
    product_id: int

class PriceHistoryResponse(PriceHistoryBase):
    id: int
    product_id: int
    checked_at: datetime

    class Config:
        from_attributes = True
