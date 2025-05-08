# app/core/config.py
import os
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Settings(BaseSettings):

    # Add type annotations for IDE support
    APP_NAME: str = "Second Certainty"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
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
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()