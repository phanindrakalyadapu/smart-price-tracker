from pydantic import BaseModel, ConfigDict
from typing import Optional

class WishlistItemResponse(BaseModel):
    product_id: int
    name: str
    url: str
    site: str
    image_url: Optional[str] = None
    current_price: Optional[float] = None
    last_updated: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
