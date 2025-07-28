# app/api/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_db
from app.core.data_scraper import SARSDataScraper
from app.core.tax_calculator import TaxCalculator


def get_tax_calculator(db: Session = Depends(get_db)):
    """Dependency to get TaxCalculator instance."""
    return TaxCalculator(db)


def get_sars_data_scraper():
    """Dependency to get SARSDataScraper instance."""
    return SARSDataScraper()
