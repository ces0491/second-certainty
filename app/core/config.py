# app/core/config.py - Fixed version
import os
import time
import logging
from typing import Optional, List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.utils.logging_utils import setup_logging, get_logger

class Settings(BaseSettings):
    """Application settings with proper Pydantic v2 configuration."""
    
    # Core app settings
    APP_NAME: str = "Second Certainty"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # Required settings
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # SARS related settings
    SARS_WEBSITE_URL: str = "https://www.sars.gov.za"
    
    # Optional database settings
    DATABASE_POOL_SIZE: Optional[int] = 10
    DATABASE_MAX_OVERFLOW: Optional[int] = 20
    DATABASE_POOL_TIMEOUT: Optional[int] = 30
    
    # Security settings
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: Optional[int] = 30
    MAX_LOGIN_ATTEMPTS: Optional[int] = 5
    ACCOUNT_LOCKOUT_DURATION: Optional[int] = 30
    
    # Environment
    ENVIRONMENT: Optional[str] = "development"
    
    # CORS settings
    CORS_ORIGINS: Optional[str] = "http://localhost:3000"
    
    # Rate limiting
    ENABLE_RATE_LIMITING: Optional[bool] = True
    DEFAULT_RATE_LIMIT: Optional[int] = 100
    AUTH_RATE_LIMIT: Optional[int] = 5
    
    # File upload settings
    MAX_FILE_SIZE: Optional[int] = 10485760  # 10MB
    UPLOAD_DIR: Optional[str] = "uploads"
    ALLOWED_FILE_TYPES: Optional[str] = ".pdf,.jpg,.jpeg,.png"
    
    # Logging settings
    LOG_LEVEL: Optional[str] = "INFO"
    LOG_FILE: Optional[str] = "logs/app.log"
    ENABLE_QUERY_LOGGING: Optional[bool] = False
    SLOW_QUERY_THRESHOLD: Optional[float] = 1.0
    
    # Scraping settings
    SCRAPING_TIMEOUT: Optional[int] = 30
    SCRAPING_RETRIES: Optional[int] = 3
    
    # Pydantic v2 configuration
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"  # Allow extra fields from environment
    )

# Initialize settings
settings = Settings()

# Set up application logging
logger = setup_logging(
    app_name="second_certainty",
    log_level=logging.DEBUG if settings.DEBUG else logging.INFO
)

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session with retry logic."""
    db = SessionLocal()
    retries = 3
    while retries > 0:
        try:
            # Properly use the text() function for raw SQL
            db.execute(text("SELECT 1"))
            break
        except SQLAlchemyError as e:
            retries -= 1
            if retries == 0:
                logger.error(f"Failed to connect to database after 3 attempts: {e}")
                raise
            logger.warning(f"Database connection failed. Retrying... ({retries} attempts left)")
            time.sleep(1)
    
    try:
        yield db
    finally:
        db.close()