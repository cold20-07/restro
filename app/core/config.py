from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings configuration"""
    
    # Application settings
    app_name: str = "QR Code Ordering System"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    version: str = "1.0.0"
    
    # API settings
    api_v1_prefix: str = "/api"
    
    # Supabase configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # JWT settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    allowed_origins: List[str] = ["*"]  # Configure properly for production
    
    # Database settings
    database_url: Optional[str] = None

settings = Settings()