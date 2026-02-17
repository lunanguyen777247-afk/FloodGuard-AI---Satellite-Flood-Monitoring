from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application
    APP_NAME: str = "FloodGuard-AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # API
    API_V1_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    
    # Google Earth Engine
    GEE_SERVICE_ACCOUNT: str
    GEE_PRIVATE_KEY_PATH: str
    
    # Google Gemini AI
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # External APIs
    OPENWEATHER_API_KEY: Optional[str] = None
    GPM_API_KEY: Optional[str] = None
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    
    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHANNEL_ID: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Data Processing
    MAX_WORKERS: int = 4
    CACHE_TTL: int = 3600  # seconds
    DATA_REFRESH_INTERVAL: int = 21600  # 6 hours
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    TILES_CACHE_DIR: str = "./cache/tiles"
    
    # GEE Processing
    GEE_MAX_PIXELS: int = 1e9
    GEE_SCALE: int = 30  # meters
    
    # Vietnam specific regions
    VIETNAM_PROVINCES: List[str] = [
        "Quảng Trị", "Thừa Thiên Huế", "Quảng Bình", 
        "Hà Tĩnh", "Nghệ An", "Thanh Hóa"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Initialize directories
def init_directories():
    """Create necessary directories if they don't exist"""
    settings = get_settings()
    dirs = [
        settings.UPLOAD_DIR,
        settings.REPORTS_DIR,
        settings.TILES_CACHE_DIR,
        os.path.dirname(settings.GEE_PRIVATE_KEY_PATH) if settings.GEE_PRIVATE_KEY_PATH else None
    ]
    
    for dir_path in dirs:
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
