from sqlalchemy import Column, Integer, ForeignKey, DateTime, Sequence, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base, TESTING

if not TESTING:
    wishlist_id_seq = Sequence('wishlist_id_seq', start=1, increment=1)

class Wishlist(Base):
    __tablename__ = "wishlist"

    if TESTING:
        id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    else:
        id = Column(Integer, wishlist_id_seq, primary_key=True, server_default=wishlist_id_seq.next_value())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="wishlists")
    product = relationship("Product", back_populates="wishlists")

