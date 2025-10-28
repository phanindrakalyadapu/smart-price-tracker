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

is_render = os.getenv("RENDER") == "true"

if is_render:
    # ✅ SQLite for unit tests
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    # ✅ Oracle for local/production
    DATABASE_URL = (
        "postgresql://smart_price_tracker_user:HT7GULfv4A8orIcLSJlHf3c0cIiA4OGK@dpg-d40jn263jp1c73ehkbg0-a.oregon-postgres.render.com/smart_price_tracker"
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
