from sqlalchemy import Column, Integer, String, DateTime, func, Sequence
from app.database import Base, TESTING
print(f"🧪 MODEL TESTING FLAG: {TESTING}")
from sqlalchemy.orm import relationship

if not TESTING:
    user_id_seq = Sequence('users_id_seq', start=1, increment=1)

class User(Base):
    __tablename__ = "users"

    if TESTING:
        id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    else:
        id = Column(Integer, user_id_seq, primary_key=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    wishlists = relationship("Wishlist", back_populates="user")
    


