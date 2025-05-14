# app/core/config.py
import os
import time  # Make sure to import time for sleep
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, text  # Add text import
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError  # Add this import for error handling

# Import the logger from logging utils
from app.utils.logging_utils import get_logger

class Settings(BaseSettings):

    # Add type annotations for IDE support
    APP_NAME: str = "Second Certainty"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    DEBUG: bool = False

    # Database settings - use environment variable with fallback
    DATABASE_URL: str
    
    # SARS related settings
    SARS_WEBSITE_URL: str = "https://www.sars.gov.za"
    
    # Authentication - require these settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow case-insensitive environment variables
        case_sensitive = False
settings = Settings()

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