# app/core/data_scraper.py
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.core.scraping.sars_service import SARSDataService

class SARSDataScraper:
    """
    Enhanced scraper for South African Revenue Service tax tables and rates.
    This is a compatibility wrapper around the new modular scraping components.
    """
    
    def __init__(self):
        """Initialize the scraper."""
        pass
    
    async def update_tax_data(self, db: Session, tax_year: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        Update tax data in the database for a specific tax year.
        
        Args:
            db: Database session
            tax_year: The tax year to update (defaults to current tax year)
            force: Whether to override existing data
        
        Returns:
            Dictionary containing the updated tax data
        """
        service = SARSDataService(db)
        return await service.update_tax_data(tax_year, force)