from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, func, Sequence, Text
from sqlalchemy.orm import relationship
from app.database import Base

price_history_id_seq = Sequence('price_history_id_seq', start=1, increment=1)
class PriceHistory(Base):
    __tablename__ = "price_history"

    # 👇 SIMPLIFIED: Use the same pattern as your Product model
    id = Column(Integer, price_history_id_seq, primary_key=True, server_default=price_history_id_seq.next_value())
    
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    price = Column(Float, nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    product = relationship("Product", back_populates="price_history")
    ai_summary = Column(Text, nullable=True)