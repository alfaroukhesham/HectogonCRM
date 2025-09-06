import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List


# Load environment variables
ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')


class Settings:
    """Application settings loaded from environment variables."""
    
    # Database settings
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
    DB_NAME: str = os.environ.get('DB_NAME', 'tiny_crm')
    
    # Redis settings
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_HOST: str = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.environ.get('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.environ.get('REDIS_DB', '0'))
    REDIS_PASSWORD: str = os.environ.get('REDIS_PASSWORD', '')
    REDIS_USERNAME: str = os.environ.get('REDIS_USERNAME', '')
    REDIS_SSL: bool = os.environ.get('REDIS_SSL', 'false').lower() == 'true'
    REDIS_SSL_CERT_REQS: str = os.environ.get('REDIS_SSL_CERT_REQS', 'required')
    REDIS_SSL_CA_CERTS: str = os.environ.get('REDIS_SSL_CA_CERTS', '')
    REDIS_SSL_CERTFILE: str = os.environ.get('REDIS_SSL_CERTFILE', '')
    REDIS_SSL_KEYFILE: str = os.environ.get('REDIS_SSL_KEYFILE', '')
    REDIS_SSL_CHECK_HOSTNAME: bool = os.environ.get('REDIS_SSL_CHECK_HOSTNAME', 'true').lower() == 'true'
    REDIS_MAX_CONNECTIONS: int = int(os.environ.get('REDIS_MAX_CONNECTIONS', '20'))
    REDIS_RETRY_ON_TIMEOUT: bool = os.environ.get('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
    REDIS_SOCKET_CONNECT_TIMEOUT: int = int(os.environ.get('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
    REDIS_SOCKET_KEEPALIVE: bool = os.environ.get('REDIS_SOCKET_KEEPALIVE', 'true').lower() == 'true'
    
    # Cache TTL settings (in seconds)
    USER_MEMBERSHIP_CACHE_TTL: int = int(os.environ.get('USER_MEMBERSHIP_CACHE_TTL', '3600'))  # 1 hour
    DASHBOARD_CACHE_TTL: int = int(os.environ.get('DASHBOARD_CACHE_TTL', '1800'))  # 30 minutes
    
    # API settings
    API_PREFIX: str = "/api"
    
    # CORS settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # Allow all origins for development
    ]
    ALLOWED_METHODS: list = ["*"] 
    ALLOWED_HEADERS: list = ["*"]
    ALLOW_CREDENTIALS: bool = True
    
    # JWT settings
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY')
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    
    # OAuth2 settings
    GOOGLE_CLIENT_ID: str = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET: str = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    FACEBOOK_CLIENT_ID: str = os.environ.get('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET: str = os.environ.get('FACEBOOK_CLIENT_SECRET')
    FACEBOOK_API_VERSION: str = os.environ.get('FACEBOOK_API_VERSION', 'v21.0')
    
    TWITTER_CLIENT_ID: str = os.environ.get('TWITTER_CLIENT_ID')
    TWITTER_CLIENT_SECRET: str = os.environ.get('TWITTER_CLIENT_SECRET')
    
    # Email settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@tinycrm.com")
    FROM_NAME: str = os.getenv("FROM_NAME", "Tiny CRM")
    
    # Frontend URL for OAuth redirects and email links
    FRONTEND_URL: str = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    
    # Security settings
    PASSWORD_MIN_LENGTH: int = 8
    BCRYPT_ROUNDS: int = 12
    
    # Logging
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        # OAuth validation disabled for testing
        # if not self.GOOGLE_CLIENT_ID:
        #     raise ValueError("GOOGLE_CLIENT_ID environment variable is required")
        # if not self.GOOGLE_CLIENT_SECRET:
        #     raise ValueError("GOOGLE_CLIENT_SECRET environment variable is required")
        # if not self.FACEBOOK_CLIENT_ID:
        #     raise ValueError("FACEBOOK_CLIENT_ID environment variable is required")

# Global settings instance
settings = Settings() 