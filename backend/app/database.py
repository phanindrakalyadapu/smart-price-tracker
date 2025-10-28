import os
import oracledb
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Initialize Oracle Client safely (optional for THIN mode) ---
# If you have Oracle Instant Client installed, uncomment and set the correct path.
# Otherwise, oracledb will automatically use THIN mode.
try:
    oracledb.init_oracle_client()  # no path → auto THIN mode fallback
except Exception:
    # This avoids "cannot initialize multiple times" errors when reloading
    pass

# --- Detect testing mode ---
TESTING = os.getenv("TESTING", "false").lower() == "true"

if TESTING:
    # ✅ SQLite for unit tests
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # ✅ Oracle for local/production
    DATABASE_URL = (
        "oracle+oracledb://price_tracker:Phani12@localhost:1521/?service_name=XEPDB1"
    )
    engine = create_engine(DATABASE_URL, echo=True, future=True)

# --- Session setup ---
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# --- Dependency for FastAPI ---
def get_db():
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
