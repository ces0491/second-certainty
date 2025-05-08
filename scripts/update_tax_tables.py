#!/usr/bin/env python3
"""
Script to update tax tables by scraping the SARS website.
Can be run independently or as a scheduled task.

Usage:
    python update_tax_tables.py [--force]
    
Arguments:
    --force: Force update even if tax data for the current year exists
"""

import asyncio
import argparse
import sys
import os
import logging
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.config import get_db, engine
from app.models.tax_models import Base, TaxBracket
from app.core.data_scraper import SARSDataScraper
from app.utils.tax_utils import get_tax_year

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"tax_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger(__name__)

async def update_tax_tables(force: bool = False):
    """
    Update tax tables by scraping the SARS website.
    
    Args:
        force: Force update even if tax data for the current year exists
    """
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize the scraper
        scraper = SARSDataScraper()
        tax_year = get_tax_year()
        
        # Check if tax data already exists for the current tax year
        existing_data = db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).first()
        
        if existing_data and not force:
            logger.info(f"Tax data for {tax_year} already exists. Use --force to update anyway.")
            return
        
        # Update tax data
        logger.info(f"Updating tax data for {tax_year}...")
        result = await scraper.update_tax_data(db)
        
        # Log the results
        logger.info(f"Tax data update successful for {tax_year}")
        logger.info(f"Updated {len(result['brackets'])} tax brackets")
        logger.info(f"Updated rebates: Primary={result['rebates']['primary']}, Secondary={result['rebates']['secondary']}, Tertiary={result['rebates']['tertiary']}")
        logger.info(f"Updated thresholds: Below 65={result['thresholds']['below_65']}, 65-74={result['thresholds']['age_65_to_74']}, 75+={result['thresholds']['age_75_plus']}")
        logger.info(f"Updated medical credits: Main member={result['medical_credits']['main_member']}, Additional member={result['medical_credits']['additional_member']}")
        
        print(f"Tax data for {tax_year} has been successfully updated.")
        
    except Exception as e:
        logger.error(f"Error updating tax data: {e}", exc_info=True)
        print(f"Error updating tax data: {e}")
        raise
    finally:
        db.close()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Update tax tables from SARS website")
    parser.add_argument("--force", action="store_true", help="Force update even if tax data exists")
    args = parser.parse_args()
    
    try:
        # Ensure database tables exist
        Base.metadata.create_all(bind=engine)
        
        # Run the update
        asyncio.run(update_tax_tables(args.force))
    except KeyboardInterrupt:
        logger.info("Update cancelled by user")
        print("Update cancelled.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()