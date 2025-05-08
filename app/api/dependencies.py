# app/api/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.config import get_db
from app.core.tax_calculator import TaxCalculator
from app.core.data_scraper import SARSDataScraper
from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user
from app.models.tax_models import UserProfile

def get_tax_calculator(db: Session = Depends(get_db)):
    """Dependency to get TaxCalculator instance."""
    return TaxCalculator(db)

def get_sars_data_scraper():
    """Dependency to get SARSDataScraper instance."""
    return SARSDataScraper()

def get_current_admin_user(current_user: UserProfile = Depends(get_current_user)):
    """Dependency to get current admin user."""
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user