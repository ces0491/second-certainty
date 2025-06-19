# app/core/config.py - Fixed version
import logging
import os
import time
from typing import List, Optional
from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from app.utils.logging_utils import get_logger, setup_logging
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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  #1 week
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
    # File upload settings - Fixed to handle string values with comments
    MAX_FILE_SIZE: Optional[int] = 10485760  #10MB
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
    # Validator to clean up integer fields that might have comments
    @field_validator(
        "MAX_FILE_SIZE",
        "DATABASE_POOL_SIZE",
        "DATABASE_MAX_OVERFLOW",
        "DATABASE_POOL_TIMEOUT",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
        "MAX_LOGIN_ATTEMPTS",
        "ACCOUNT_LOCKOUT_DURATION",
        "DEFAULT_RATE_LIMIT",
        "AUTH_RATE_LIMIT",
        "SCRAPING_TIMEOUT",
        "SCRAPING_RETRIES",
        mode="before",
    )
    @classmethod
    def parse_int_with_comments(cls, v):
        """Parse integer values that might have comments."""
        if isinstance(v, str):
            # Remove comments and whitespace
            v = v.split("  # ")[0].strip()
            if v.isdigit():
                return int(v)
            # If it's not all digits, try to extract just the number part
            import re
            match = re.match(r"^\d+", v)
            if match:
                return int(match.group())
        return v
    # Pydantic v2 configuration
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  #Allow extra fields from environment
    )
# Initialize settings with error handling
try:
    settings = Settings()
except Exception as e:
    print(f"Error loading settings: {e}")
    print("Creating minimal settings for debugging...")
    # Create minimal settings for debugging
    class MinimalSettings:
        APP_NAME = "Second Certainty"
        APP_VERSION = "1.0.0"
        API_PREFIX = "/api"
        DEBUG = True
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./second_certainty.db")
        SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-debugging")
        ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
        SARS_WEBSITE_URL = "https://www.sars.gov.za"
        MAX_FILE_SIZE = 10485760
        UPLOAD_DIR = "uploads"
        LOG_LEVEL = "INFO"
        ENVIRONMENT = "development"
    settings = MinimalSettings()
# Set up application logging
logger = setup_logging(
    app_name="second_certainty", log_level=logging.DEBUG if getattr(settings, "DEBUG", False) else logging.INFO
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
