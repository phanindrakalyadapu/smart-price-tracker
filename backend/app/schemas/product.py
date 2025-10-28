from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class ProductIngestRequest(BaseModel):
    user_id: int
    url: HttpUrl
    site: str = "auto"  # 'amazon', 'flipkart', 'auto'

class ProductBase(BaseModel):
    name: str
    url: str
    site: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[float] = None
    color: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)