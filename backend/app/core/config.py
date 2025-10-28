from pydantic_settings import BaseSettings
from pathlib import Path
import os

# ✅ Absolute path to ensure .env is loaded correctly
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    class Config:
        env_file = ENV_PATH       # ✅ absolute path
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()

# ✅ Debug print to confirm values are loaded
print("🔧 Loaded .env from:", ENV_PATH)
print("📨 MAIL_SERVER:", settings.MAIL_SERVER)
print("📨 MAIL_PORT:", settings.MAIL_PORT)
print("📨 MAIL_USERNAME:", settings.MAIL_USERNAME)
