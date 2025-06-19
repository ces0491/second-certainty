# app/api/dependencies.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_db
from app.core.data_scraper import SARSDataScraper
from app.core.tax_calculator import TaxCalculator
from app.models.tax_models import UserProfile


def get_tax_calculator(db: Session = Depends(get_db)):
    """Dependency to get TaxCalculator instance."""
    return TaxCalculator(db)


def get_sars_data_scraper():
    """Dependency to get SARSDataScraper instance."""
    return SARSDataScraper()
