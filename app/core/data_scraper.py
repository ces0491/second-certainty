# app/core/data_scraper.py (updated with logging)
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.core.scraping.sars_service import SARSDataService
from app.utils.logging_utils import get_logger

# Get module logger
logger = get_logger("data_scraper")

class SARSDataScraper:
    """
    Enhanced scraper for South African Revenue Service tax tables and rates.
    This is a compatibility wrapper around the new modular scraping components.
    """
    
    def __init__(self):
        """Initialize the scraper."""
        logger.debug("SARSDataScraper initialized")
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
        logger.info(f"Updating tax data for {tax_year if tax_year else 'current tax year'}")
        logger.debug(f"Force update: {force}")
        
        service = SARSDataService(db)
        result = await service.update_tax_data(tax_year, force)
        
        logger.info(f"Tax data update completed successfully")
        return result