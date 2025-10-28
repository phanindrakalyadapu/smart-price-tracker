import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ----------------------------
# 1️⃣ Force TEST mode
# ----------------------------
os.environ["TESTING"] = "true"

# Ensure the project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.main import app
from app.database import Base, get_db

# ✅ Explicitly import models early
from app import models

# ----------------------------
# 2️⃣ SQLite test DB setup
# ----------------------------
SQLITE_URL = "sqlite:///./test.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create and tear down the SQLite schema for testing"""
    print("🧪 Creating SQLite schema...")
    # Ensure all tables from models are loaded before creating schema
    models  # just referencing guarantees import execution
    Base.metadata.drop_all(bind=engine)
    print("📋 Tables in metadata before create_all:", Base.metadata.tables.keys())
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    print("🧹 Dropped SQLite schema.")

@pytest.fixture(scope="function")
def db_session():
    """Provide a transactional test session"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Provide a FastAPI test client using SQLite test DB"""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
