import os
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')


class Settings:
    """Application settings loaded from environment variables."""
    
    # Database settings
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
    DB_NAME: str = os.environ.get('DB_NAME', 'tiny_crm')
    
    # API settings
    API_PREFIX: str = "/api"
    
    # CORS settings
    ALLOWED_ORIGINS: list = ["*"]
    ALLOWED_METHODS: list = ["*"] 
    ALLOWED_HEADERS: list = ["*"]
    ALLOW_CREDENTIALS: bool = True
    
    # Logging
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')


# Global settings instance
settings = Settings() 