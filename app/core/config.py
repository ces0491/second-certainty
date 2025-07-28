# app/core/config.py
import logging
import os
import time

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.utils.logging_utils import setup_logging


class Settings(BaseSettings):
    """Application settings with proper Pydantic v2 configuration."""

    # Core app settings
    APP_NAME: str = "Second Certainty"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = False

    # Required settings with defaults for development
    DATABASE_URL: str = "sqlite:///./second_certainty.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # SARS related settings
    SARS_WEBSITE_URL: str = "https://www.sars.gov.za"

    # Optional database settings
    DATABASE_POOL_SIZE: int | None = 10
    DATABASE_MAX_OVERFLOW: int | None = 20
    DATABASE_POOL_TIMEOUT: int | None = 30

    # Security settings
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int | None = 30
    MAX_LOGIN_ATTEMPTS: int | None = 5
    ACCOUNT_LOCKOUT_DURATION: int | None = 30

    # Environment
    ENVIRONMENT: str | None = "development"

    # CORS settings
    CORS_ORIGINS: str | None = "http://localhost:3000"

    # Rate limiting
    ENABLE_RATE_LIMITING: bool | None = True
    DEFAULT_RATE_LIMIT: int | None = 100
    AUTH_RATE_LIMIT: int | None = 5

    # File upload settings - Fixed to handle string values with comments
    MAX_FILE_SIZE: int | None = 10485760  # 10MB
    UPLOAD_DIR: str | None = "uploads"
    ALLOWED_FILE_TYPES: str | None = ".pdf,.jpg,.jpeg,.png"

    # Logging settings
    LOG_LEVEL: str | None = "INFO"
    LOG_FILE: str | None = "logs/app.log"
    ENABLE_QUERY_LOGGING: bool | None = False
    SLOW_QUERY_THRESHOLD: float | None = 1.0

    # Scraping settings
    SCRAPING_TIMEOUT: int | None = 30
    SCRAPING_RETRIES: int | None = 3

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

    # Pydantic v2 configuration - Fixed: Use SettingsConfigDict
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow extra fields from environment
    )


# Initialize settings with error handling
try:
    settings = Settings()  # Pydantic will automatically load from .env and environment
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
