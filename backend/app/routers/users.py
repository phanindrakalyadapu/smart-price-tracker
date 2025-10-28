import re
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
import asyncio
from app.services.email_utils import send_welcome_email

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin

router = APIRouter(prefix="/users", tags=["Users"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password(password: str):
    """Allow only ASCII characters and special symbols, enforce 5–72 char limit"""
    pattern = r'^[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};\'\\:"|<,./<>?`~]+$'
    if not re.match(pattern, password):
        raise HTTPException(
            status_code=400,
            detail="Password can only contain letters, numbers, and special characters (no emojis or spaces)."
        )
    if len(password) < 5 or len(password) > 72:
        raise HTTPException(status_code=400, detail="Password must be between 5 and 72 characters.")


def hash_password(password: str) -> str:
    sha256_hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return pwd_context.hash(sha256_hashed)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    sha256_hashed = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return pwd_context.verify(sha256_hashed, hashed_password)


# ✅ Create new user
@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Create user, ensure email uniqueness, and send welcome email."""
    validate_password(user.password)

    # Check if user exists
    clean_email = user.email.strip().lower()

    # Always start with a clean transaction
    db.rollback()  # ✅ ensures no old transaction left open

     # Check if user already exists
    from sqlalchemy import func
    existing = db.query(User).filter(func.lower(User.email) == clean_email).first()
    print(f"📧 Checking email: {clean_email}")
    print(f"🔍 Found existing: {existing}")


    # Hash password
    hashed_pw = hash_password(user.password)

    # Create new user record
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=hashed_pw,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # ✅ Send welcome email asynchronously
        background_tasks.add_task(send_welcome_email, new_user.email, new_user.first_name)
        return new_user
    
    except IntegrityError:
        db.rollback()
        print("❌ Integrity error:", str(e))
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        db.rollback()
        print("❌ Unknown error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Get a single user
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    return user


# ✅ Get all users
@router.get("/", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()

from fastapi import status
from app.schemas.user import UserLogin

@router.post("/login")
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    }

