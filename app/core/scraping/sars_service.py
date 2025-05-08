# app/core/scraping/sars_service.py
import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, Tuple

from app.utils.tax_utils import get_tax_year
from app.core.scraping.web_client import SARSWebClient
from app.core.scraping.tax_parser import TaxDataParser
from app.core.scraping.tax_repository import TaxDataRepository
from app.core.scraping.tax_provider import TaxDataProvider

logger = logging.getLogger(__name__)

class SARSTaxException(Exception):
    """Exception raised for errors in SARS tax data scraping."""
    pass

class SARSDataService:
    """Service for coordinating SARS tax data scraping and storage."""
    
    def __init__(self, db: Session):
        """
        Initialize the SARS data service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.web_client = SARSWebClient()
        self.tax_parser = TaxDataParser()
        self.tax_repository = TaxDataRepository(db)
        self.tax_provider = TaxDataProvider()
        self.success_count = 0
        self.error_count = 0
    
    async def update_tax_data(self, tax_year: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        Update tax data for a specific tax year.
        
        Args:
            tax_year: The tax year to update (default: current tax year)
            force: Whether to override existing data
            
        Returns:
            Dictionary containing the updated tax data
            
        Raises:
            SARSTaxException: If tax data could not be updated
        """
        if not tax_year:
            tax_year = get_tax_year()
        
        logger.info(f"Starting tax data update for {tax_year}")
        
        # Check if data already exists
        if not force and self.tax_repository.check_tax_data_exists(tax_year):
            logger.info(f"Tax data for {tax_year} already exists. Use force=True to override.")
            raise SARSTaxException(f"Tax data for {tax_year} already exists")
        
        # Clear existing data if force is True
        if force:
            self.tax_repository.clear_tax_data(tax_year)
        
        # Try multiple approaches in sequence
        data = await self.try_current_page(tax_year)
        if not data:
            data = await self.try_archive_page(tax_year)
        if not data:
            data = await self.try_previous_year_data(tax_year)
        if not data:
            data = self.tax_provider.get_manual_tax_data(tax_year)
        
        # Save data to database
        success, error = self.tax_repository.save_tax_data(data)
        if not success:
            raise SARSTaxException(f"Failed to save tax data: {error}")
        
        return data
    
    async def try_current_page(self, tax_year: str) -> Optional[Dict[str, Any]]:
        """
        Try to get tax data from the current tax rates page.
        
        Args:
            tax_year: The tax year to get data for
            
        Returns:
            Dictionary containing tax data, or None if not found
        """
        logger.info(f"Attempting to get {tax_year} tax data from current page")
        
        try:
            # Fetch current page
            html_content = await self.web_client.fetch_current_tax_page()
            if not html_content:
                return None
            
            # Try to find section specific to this tax year
            year_content = self.tax_parser.find_year_section(html_content, tax_year)
            if year_content:
                logger.info(f"Found specific section for {tax_year}")
                html_content = year_content
            
            # Extract tax data
            brackets = self.tax_parser.extract_tax_brackets(html_content, tax_year)
            
            if not brackets:
                logger.warning(f"No tax brackets found for {tax_year} on current page")
                return None
            
            rebates = self.tax_parser.extract_tax_rebates(html_content, tax_year)
            thresholds = self.tax_parser.extract_tax_thresholds(html_content, tax_year)
            medical_credits = self.tax_parser.extract_medical_tax_credits(html_content, tax_year)
            
            self.success_count += 1
            logger.info(f"Successfully extracted {tax_year} tax data from current page")
            
            return {
                "tax_year": tax_year,
                "brackets": brackets,
                "rebates": rebates,
                "thresholds": thresholds,
                "medical_credits": medical_credits
            }
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error extracting tax data from current page: {e}")
            return None
    
    async def try_archive_page(self, tax_year: str) -> Optional[Dict[str, Any]]:
        """
        Try to get tax data from the archive page.
        
        Args:
            tax_year: The tax year to get data for
            
        Returns:
            Dictionary containing tax data, or None if not found
        """
        logger.info(f"Attempting to get {tax_year} tax data from archive")
        
        try:
            # Fetch archive page
            archive_html = await self.web_client.fetch_archive_page()
            if not archive_html:
                return None
            
            # Find link for specific tax year
            archive_link = self.tax_parser.find_archive_link(archive_html, tax_year)
            if not archive_link:
                logger.warning(f"No archive link found for {tax_year}")
                return None
            
            # Fetch specific archive page
            archive_content = await self.web_client.fetch_specific_archive_page(archive_link)
            if not archive_content:
                return None
            
            # Extract tax data
            brackets = self.tax_parser.extract_tax_brackets(archive_content, tax_year)
            
            if not brackets:
                logger.warning(f"No tax brackets found for {tax_year} in archive")
                return None
            
            rebates = self.tax_parser.extract_tax_rebates(archive_content, tax_year)
            thresholds = self.tax_parser.extract_tax_thresholds(archive_content, tax_year)
            medical_credits = self.tax_parser.extract_medical_tax_credits(archive_content, tax_year)
            
            self.success_count += 1
            logger.info(f"Successfully extracted {tax_year} tax data from archive")
            
            return {
                "tax_year": tax_year,
                "brackets": brackets,
                "rebates": rebates,
                "thresholds": thresholds,
                "medical_credits": medical_credits
            }
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error extracting tax data from archive: {e}")
            return None
    
    async def try_previous_year_data(self, tax_year: str) -> Optional[Dict[str, Any]]:
        """
        Try to use data from the previous tax year.
        
        Args:
            tax_year: The tax year to get data for
            
        Returns:
            Dictionary containing tax data, or None if not found
        """
        logger.info(f"Attempting to use previous year data for {tax_year}")
        
        try:
            # Calculate previous tax year
            year_start = int(tax_year.split('-')[0])
            year_end = int(tax_year.split('-')[1])
            previous_tax_year = f"{year_start-1}-{year_end-1}"
            
            # Get previous year data
            previous_data = self.tax_repository.get_previous_tax_year_data(previous_tax_year, tax_year)
            
            if previous_data:
                self.success_count += 1
                logger.info(f"Successfully used previous year data for {tax_year}")
                return previous_data
            
            return None
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error using previous year data: {e}")
            return None