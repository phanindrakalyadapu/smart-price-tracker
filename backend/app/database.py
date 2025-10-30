import os
import io
import zipfile
import base64
import oracledb
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv  # ✅ add this

# --- Load .env file first ---
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))  # ✅ ensures .env is loaded

# --- ENVIRONMENT ---
IS_RENDER = os.getenv("RENDER", "false").lower() == "true"
ORA_USER = os.getenv("ORA_USER")
ORA_PASSWORD = os.getenv("ORA_PASSWORD")
ORA_DSN = os.getenv("ORA_DSN")  # from tnsnames.ora (e.g., smartprice_high)
INSTANT_CLIENT_DIR = os.getenv("INSTANT_CLIENT_DIR")  # e.g., D:\instantclient_19_28
WALLET_DIR = os.getenv("WALLET_DIR")  # e.g., D:\Phanindra\smart-price-tracker\backend\wallet

# --- FUNCTION: Extract wallet for Render ---
def _ensure_wallet_on_render():
    """Decode WALLET_ZIP_B64 and extract wallet to /tmp or local folder on Render."""
    wallet_dir = os.path.join(os.getcwd(), "wallet")
    if not os.path.isdir(wallet_dir):
        os.makedirs(wallet_dir, exist_ok=True)

    expected_files = ["tnsnames.ora", "sqlnet.ora"]
    if all(os.path.exists(os.path.join(wallet_dir, f)) for f in expected_files):
        return wallet_dir

    b64_zip = os.getenv("WALLET_ZIP_B64")
    if not b64_zip:
        raise RuntimeError("WALLET_ZIP_B64 not found in environment (Render)")

    raw_data = base64.b64decode(b64_zip)
    with zipfile.ZipFile(io.BytesIO(raw_data), "r") as zf:
        zf.extractall(wallet_dir)

    # Sanity check
    for fn in expected_files:
        path = os.path.join(wallet_dir, fn)
        if not os.path.exists(path):
            raise RuntimeError(f"Wallet file missing after unzip: {fn}")

    return wallet_dir


# --- ORACLE CLIENT INITIALIZATION ---
if IS_RENDER:
    # Render = THIN mode (no instant client)
    wallet_path = _ensure_wallet_on_render()
    print(f"🌐 Render: Using THIN mode with wallet at {wallet_path}")
    CONNECT_ARGS = {"config_dir": wallet_path, "dsn": ORA_DSN}
else:
    # Local = THICK mode (requires instant client + wallet)
    if not INSTANT_CLIENT_DIR or not WALLET_DIR:
        raise RuntimeError("Set INSTANT_CLIENT_DIR and WALLET_DIR in your local .env")

    # Initialize Oracle Instant Client (only once per process)
    oracledb.init_oracle_client(lib_dir=INSTANT_CLIENT_DIR, config_dir=WALLET_DIR)
    print(f"💻 Local: THICK mode initialized.\nInstant Client: {INSTANT_CLIENT_DIR}\nWallet: {WALLET_DIR}")
    CONNECT_ARGS = {"dsn": ORA_DSN}


# --- VALIDATE MANDATORY VARIABLES ---
if not ORA_USER or not ORA_PASSWORD or not ORA_DSN:
    raise RuntimeError("Missing ORA_USER / ORA_PASSWORD / ORA_DSN in .env")

# --- BUILD SQLALCHEMY ENGINE ---
DATABASE_URL = f"oracle+oracledb://{ORA_USER}:{ORA_PASSWORD}@"

engine = create_engine(
    DATABASE_URL,
    connect_args=CONNECT_ARGS,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# --- FUNCTION: GET DB SESSION ---
def get_db():
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()