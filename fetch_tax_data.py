#!/usr/bin/env python3
"""
SARS Tax Data Retrieval Tool

This script fetches tax data from the SARS website and stores it in the database.
It consolidates all tax data fetching functionality and provides multiple fallback methods.

Usage:
    python fetch_tax_data.py [--year YYYY-YYYY] [--force] [--manual]

Options:
    --year YYYY-YYYY    Specify tax year in format "2024-2025" (default: current tax year)
    --force             Override existing data for the specified tax year
    --manual            Skip web scraping and use manual data entry
"""

import sys
import os
import argparse
import asyncio
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.config import get_db
from app.utils.tax_utils import get_tax_year
from app.utils.logging_utils import setup_logging
from app.core.scraping.sars_service import SARSDataService

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Set up logging
logger = setup_logging(
    app_name="tax_data_fetcher", 
    log_level=logging.INFO
)

async def fetch_and_save_tax_data(tax_year: Optional[str] = None, force: bool = False, manual: bool = False) -> bool:
    """
    Main function to fetch tax data and save it to the database.
    
    Args:
        tax_year: The tax year to fetch data for (default: current tax year)
        force: Whether to override existing data
        manual: Whether to use manual data entry instead of scraping
        
    Returns:
        True if the operation was successful, False otherwise
    """
    # Use current tax year if not specified
    if not tax_year:
        tax_year = get_tax_year()
    
    logger.info(f"Starting tax data fetch for {tax_year}")
    logger.info(f"Force override: {force}")
    logger.info(f"Manual data: {manual}")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create the service and run it
        service = SARSDataService(db)
        
        if manual:
            # Use the manual tax data provider
            from app.core.scraping.tax_provider import TaxDataProvider
            provider = TaxDataProvider()
            data = provider.get_manual_tax_data(tax_year)
            
            # Save the data to the database
            from app.core.scraping.tax_repository import TaxDataRepository
            repository = TaxDataRepository(db)
            success, error = repository.save_tax_data(data)
            
            if success:
                logger.info(f"Successfully saved manual tax data for {tax_year}")
                return True
            else:
                logger.error(f"Failed to save manual tax data: {error}")
                return False
        else:
            # Use the SARS data service
            result = await service.update_tax_data(tax_year, force)
            
            if result:
                logger.info(f"Successfully processed tax data for {tax_year}")
                return True
            else:
                logger.warning(f"No data returned from SARS data service for {tax_year}")
                return False
    except Exception as e:
        logger.error(f"Error processing tax data: {e}", exc_info=True)
        return False
    finally:
        db.close()
        logger.info("Database session closed")

async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Fetch tax data from SARS website and save to database")
    parser.add_argument("--year", help="Tax year in format YYYY-YYYY, e.g., 2024-2025")
    parser.add_argument("--force", action="store_true", help="Override existing data")
    parser.add_argument("--manual", action="store_true", help="Skip scraping and use manual data")
    args = parser.parse_args()
    
    # Use current tax year if not specified
    tax_year = args.year if args.year else get_tax_year()
    
    # Set up log file with tax year in the name
    file_handler = logging.FileHandler(f"logs/tax_data_{tax_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    result = await fetch_and_save_tax_data(tax_year, args.force, args.manual)
    
    if result:
        print(f"\n✅ SUCCESS: Tax data for {tax_year} has been saved to the database")
    else:
        print(f"\n❌ ERROR: Failed to process tax data for {tax_year}")
    
    print(f"\nLog file: logs/tax_data_{tax_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

if __name__ == "__main__":
    asyncio.run(main())