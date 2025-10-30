from sqlalchemy import Column, Integer, String, DateTime, Sequence, func, Text
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import relationship

product_id_seq = Sequence('product_id_seq', start=1, increment=1)

class Product(Base):
    __tablename__ = "products"
    # 👇 add Oracle sequence for autoincrement
    id = Column(Integer, product_id_seq, primary_key=True, server_default=product_id_seq.next_value())

    name = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False)
    site = Column(String(100))
    image_url = Column(String(1000))
    color = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=func.now())
    specs_json = Column(Text, nullable=True) # store JSON.dumps of specs
    wishlists = relationship("Wishlist", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete")


