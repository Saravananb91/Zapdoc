import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        from pydantic.v1 import BaseSettings

class Settings(BaseSettings):
    # App
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OCR Extraction Agent"
    
    # Security
    # Default to "dev_secret" if not set, but warn in production
    API_KEY: str = os.getenv("API_KEY", "dev_secret_key_123")
    API_KEY_NAME: str = "X-API-KEY"
    
    # Limits
    MAX_FILE_SIZE_MB: int = 20
    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024
    MAX_PAGES: int = 10
    
    # External Services
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
    MONGO_DB: str = os.getenv("MONGO_DB", "OCR_db")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_ID: str = os.getenv("STRIPE_PRICE_ID", "")
    
    # Email (FastAPI-Mail)
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "noreply@ocragent.ai")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 25)) # Default to 25 for no-auth
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "localhost")
    MAIL_TLS: bool = False
    MAIL_SSL: bool = False
    USE_CREDENTIALS: bool = False
    VALIDATE_CERTS: bool = True
    
    # OCR Pipeline
    MAX_RETRIES: int = 3
    INITIAL_BACKOFF: float = 1.0
    LLM_TIMEOUT: int = 120
    MAX_WORKERS: int = 5

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
