#!/usr/bin/env python3
"""
SARS Tax Data Retrieval Tool

This script fetches tax data from the SARS website and stores it in the database.
It can target specific tax years and provides multiple fallback methods.

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
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
import httpx
from bs4 import BeautifulSoup
import re

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.models.tax_models import TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit
from app.core.config import get_db
from app.utils.tax_utils import get_tax_year

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"tax_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# SARS website URLs
SARS_BASE_URL = "https://www.sars.gov.za"
CURRENT_TAX_URL = f"{SARS_BASE_URL}/tax-rates/income-tax/rates-of-tax-for-individuals/"
ARCHIVE_TAX_URL = f"{SARS_BASE_URL}/tax-rates/archive-tax-rates/"

class TaxDataFetcher:
    """Tool for fetching and processing tax data from SARS website."""
    
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
    
    async def fetch_page(self, url: str) -> str:
        """Fetch HTML content from a URL with detailed error handling."""
        logger.info(f"Fetching page: {url}")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                logger.info(f"Successfully fetched page, size: {len(response.text)} bytes")
                return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error fetching {url}: {e.response.status_code} - {e.response.reason_phrase}")
            self.error_count += 1
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {url}: {e}")
            self.error_count += 1
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            self.error_count += 1
            raise
    
    async def fetch_current_year_page(self) -> Optional[str]:
        """Fetch the current tax rates page with error handling."""
        try:
            return await self.fetch_page(CURRENT_TAX_URL)
        except Exception as e:
            logger.error(f"Failed to fetch current tax page: {e}")
            return None
    
    async def fetch_archive_page(self) -> Optional[str]:
        """Fetch the archive tax rates page with error handling."""
        try:
            return await self.fetch_page(ARCHIVE_TAX_URL)
        except Exception as e:
            logger.error(f"Failed to fetch archive tax page: {e}")
            return None
    
    async def parse_tax_brackets(self, html_content: str, tax_year: str) -> List[Dict[str, Any]]:
        """Extract tax brackets from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        tax_brackets = []
        
        # Print all table headers to help debugging
        all_tables = soup.find_all('table')
        logger.info(f"Found {len(all_tables)} tables on the page")
        
        for i, table in enumerate(all_tables):
            headers = table.find_all('th')
            header_text = " ".join([h.text.strip() for h in headers])
            logger.info(f"Table {i+1} headers: {header_text}")
            
            # Check for tax bracket table
            if ("Taxable income" in header_text and "Rate" in header_text) or \
               ("Taxable income" in header_text and "tax" in header_text.lower()):
                logger.info(f"Found tax brackets table: Table {i+1}")
                
                # Extract rows from the table
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Extract income range and rates
                        income_range = cells[0].text.strip()
                        rate_text = cells[1].text.strip()
                        
                        logger.info(f"Processing row: {income_range} | {rate_text}")
                        
                        # Extract lower and upper bounds
                        income_match = re.search(r'(\d[\d\s]*)\s*[–-]\s*(\d[\d\s]*)', income_range)
                        if income_match:
                            lower_limit = int(income_match.group(1).replace(" ", ""))
                            upper_limit = int(income_match.group(2).replace(" ", ""))
                        else:
                            # Check if it's the highest bracket
                            exceed_match = re.search(r'(\d[\d\s]*)\s*and above', income_range)
                            if exceed_match:
                                lower_limit = int(exceed_match.group(1).replace(" ", ""))
                                upper_limit = None
                            else:
                                logger.warning(f"Could not parse income range: {income_range}")
                                continue
                        
                        # Extract base amount and rate
                        base_amount = 0
                        if "+" in rate_text:
                            base_match = re.search(r'(\d[\d\s]*)', rate_text)
                            if base_match:
                                base_amount = int(base_match.group(1).replace(" ", ""))
                        
                        # Extract rate percentage
                        rate_match = re.search(r'(\d+)%', rate_text)
                        if rate_match:
                            rate = int(rate_match.group(1)) / 100
                        else:
                            # If no percentage, check if it's a flat rate
                            if "18% of taxable income" in rate_text or similar_text:
                                rate = 0.18
                            else:
                                logger.warning(f"Could not parse tax rate: {rate_text}")
                                continue
                        
                        bracket = {
                            "lower_limit": lower_limit,
                            "upper_limit": upper_limit,
                            "rate": rate,
                            "base_amount": base_amount,
                            "tax_year": tax_year
                        }
                        
                        logger.info(f"Added tax bracket: {bracket}")
                        tax_brackets.append(bracket)
                
                # Once we find a valid table, break the loop
                if tax_brackets:
                    break
        
        if not tax_brackets:
            logger.error(f"No tax brackets found for {tax_year}")
        
        return tax_brackets
    
    async def parse_tax_rebates(self, html_content: str, tax_year: str) -> Dict[str, Any]:
        """Extract tax rebates from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        rebates = {
            "primary": 0,
            "secondary": 0,
            "tertiary": 0,
            "tax_year": tax_year
        }
        
        # Get the entire page text to search for rebates
        page_text = soup.get_text()
        
        # Look for rebate information
        primary_match = re.search(r'[Pp]rimary\s+rebate.*?R\s*([\d\s]+)', page_text)
        if primary_match:
            rebates["primary"] = int(primary_match.group(1).replace(" ", ""))
            logger.info(f"Found primary rebate: R{rebates['primary']}")
        
        secondary_match = re.search(r'[Ss]econdary\s+rebate.*?R\s*([\d\s]+)', page_text)
        if secondary_match:
            rebates["secondary"] = int(secondary_match.group(1).replace(" ", ""))
            logger.info(f"Found secondary rebate: R{rebates['secondary']}")
        
        tertiary_match = re.search(r'[Tt]ertiary\s+rebate.*?R\s*([\d\s]+)', page_text)
        if tertiary_match:
            rebates["tertiary"] = int(tertiary_match.group(1).replace(" ", ""))
            logger.info(f"Found tertiary rebate: R{rebates['tertiary']}")
        
        if rebates["primary"] == 0:
            logger.warning("Primary rebate not found or is zero")
        
        return rebates
    
    async def parse_tax_thresholds(self, html_content: str, tax_year: str) -> Dict[str, Any]:
        """Extract tax thresholds from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        thresholds = {
            "below_65": 0,
            "age_65_to_74": 0,
            "age_75_plus": 0,
            "tax_year": tax_year
        }
        
        # Get the entire page text to search for thresholds
        page_text = soup.get_text()
        
        # Look for threshold information
        below_65_match = re.search(r'[Bb]elow.*?65.*?R\s*([\d\s]+)', page_text)
        if below_65_match:
            thresholds["below_65"] = int(below_65_match.group(1).replace(" ", ""))
            logger.info(f"Found below 65 threshold: R{thresholds['below_65']}")
        
        age_65_match = re.search(r'[Aa]ge.*?65.*?74.*?R\s*([\d\s]+)', page_text)
        if age_65_match:
            thresholds["age_65_to_74"] = int(age_65_match.group(1).replace(" ", ""))
            logger.info(f"Found age 65-74 threshold: R{thresholds['age_65_to_74']}")
        
        age_75_match = re.search(r'[Aa]ge.*?75.*?R\s*([\d\s]+)', page_text)
        if age_75_match:
            thresholds["age_75_plus"] = int(age_75_match.group(1).replace(" ", ""))
            logger.info(f"Found age 75+ threshold: R{thresholds['age_75_plus']}")
        
        if thresholds["below_65"] == 0:
            logger.warning("Below 65 threshold not found or is zero")
        
        return thresholds
    
    async def parse_medical_tax_credits(self, html_content: str, tax_year: str) -> Dict[str, Any]:
        """Extract medical tax credits from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        credits = {
            "main_member": 0,
            "additional_member": 0,
            "tax_year": tax_year
        }
        
        # Get the entire page text to search for medical credits
        page_text = soup.get_text()
        
        # Look for medical credit information
        main_match = re.search(r'[Mm]ain\s+member.*?R\s*([\d\s\.]+)', page_text)
        if main_match:
            credits["main_member"] = float(main_match.group(1).replace(" ", ""))
            logger.info(f"Found main member credit: R{credits['main_member']}")
        
        additional_match = re.search(r'[Aa]dditional.*?member.*?R\s*([\d\s\.]+)', page_text)
        if additional_match:
            credits["additional_member"] = float(additional_match.group(1).replace(" ", ""))
            logger.info(f"Found additional member credit: R{credits['additional_member']}")
        
        if credits["main_member"] == 0:
            logger.warning("Main member medical credit not found or is zero")
        
        return credits
    
    async def find_year_section(self, html_content: str, tax_year: str) -> Optional[str]:
        """Extract section for specific tax year from the page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        year_end = tax_year.split('-')[1]
        
        # Look for headings containing the tax year
        year_headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(f"{year_end}"))
        
        for heading in year_headings:
            logger.info(f"Found heading for year {year_end}: {heading.text}")
            
            # Collect all content until next heading of same or higher level
            content = []
            current = heading.next_sibling
            
            while current and not (current.name in ['h1', 'h2', 'h3', 'h4'] and current.name <= heading.name):
                if current.name:
                    content.append(str(current))
                current = current.next_sibling
            
            return "".join(content)
        
        logger.warning(f"Could not find section for tax year {tax_year}")
        return None
    
    async def fetch_tax_data_from_current_page(self, tax_year: str) -> Optional[Dict[str, Any]]:
        """Try to fetch tax data from the current tax rates page."""
        logger.info(f"Attempting to fetch {tax_year} tax data from current page")
        
        html_content = await self.fetch_current_year_page()
        if not html_content:
            return None
        
        # Try to find section specific to this tax year
        year_content = await self.find_year_section(html_content, tax_year)
        if year_content:
            logger.info(f"Found specific section for {tax_year}")
            html_content = year_content
        
        # Extract tax data
        brackets = await self.parse_tax_brackets(html_content, tax_year)
        
        if not brackets:
            logger.warning(f"No tax brackets found for {tax_year} on current page")
            return None
        
        rebates = await self.parse_tax_rebates(html_content, tax_year)
        thresholds = await self.parse_tax_thresholds(html_content, tax_year)
        medical_credits = await self.parse_medical_tax_credits(html_content, tax_year)
        
        self.success_count += 1
        logger.info(f"Successfully extracted {tax_year} tax data from current page")
        
        return {
            "tax_year": tax_year,
            "brackets": brackets,
            "rebates": rebates,
            "thresholds": thresholds,
            "medical_credits": medical_credits
        }
    
    async def fetch_tax_data_from_archive(self, tax_year: str) -> Optional[Dict[str, Any]]:
        """Try to fetch tax data from the archive page."""
        logger.info(f"Attempting to fetch {tax_year} tax data from archive")
        
        archive_html = await self.fetch_archive_page()
        if not archive_html:
            return None
        
        # Parse archive page to find link for specific tax year
        soup = BeautifulSoup(archive_html, 'html.parser')
        year_end = tax_year.split('-')[1]
        
        # Find links related to this tax year
        archive_link = None
        for link in soup.find_all('a'):
            link_text = link.text.strip()
            if year_end in link_text and ('tax rate' in link_text.lower() or 'individual' in link_text.lower()):
                archive_link = link.get('href')
                if archive_link and not archive_link.startswith('http'):
                    archive_link = f"{SARS_BASE_URL}{archive_link}"
                logger.info(f"Found archive link for {tax_year}: {archive_link}")
                break
        
        if not archive_link:
            logger.warning(f"No archive link found for {tax_year}")
            return None
        
        # Fetch archive page
        try:
            archive_content = await self.fetch_page(archive_link)
            
            # Extract tax data
            brackets = await self.parse_tax_brackets(archive_content, tax_year)
            
            if not brackets:
                logger.warning(f"No tax brackets found for {tax_year} in archive")
                return None
            
            rebates = await self.parse_tax_rebates(archive_content, tax_year)
            thresholds = await self.parse_tax_thresholds(archive_content, tax_year)
            medical_credits = await self.parse_medical_tax_credits(archive_content, tax_year)
            
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
            logger.error(f"Error fetching or parsing archive page for {tax_year}: {e}")
            self.error_count += 1
            return None
    
    async def get_manual_tax_data(self, tax_year: str) -> Dict[str, Any]:
        """Provide manual tax data when scraping fails."""
        logger.info(f"Using manual tax data for {tax_year}")
        
        # Using 2024-2025 tax data as fallback
        brackets = [
            {"lower_limit": 1, "upper_limit": 237100, "rate": 0.18, "base_amount": 0, "tax_year": tax_year},
            {"lower_limit": 237101, "upper_limit": 370500, "rate": 0.26, "base_amount": 42678, "tax_year": tax_year},
            {"lower_limit": 370501, "upper_limit": 512800, "rate": 0.31, "base_amount": 77362, "tax_year": tax_year},
            {"lower_limit": 512801, "upper_limit": 673000, "rate": 0.36, "base_amount": 121475, "tax_year": tax_year},
            {"lower_limit": 673001, "upper_limit": 857900, "rate": 0.39, "base_amount": 179147, "tax_year": tax_year},
            {"lower_limit": 857901, "upper_limit": 1817000, "rate": 0.41, "base_amount": 251258, "tax_year": tax_year},
            {"lower_limit": 1817001, "upper_limit": None, "rate": 0.45, "base_amount": 644489, "tax_year": tax_year},
        ]
        
        rebates = {
            "primary": 17235, 
            "secondary": 9444,
            "tertiary": 3145,
            "tax_year": tax_year
        }
        
        thresholds = {
            "below_65": 95750,
            "age_65_to_74": 148217,
            "age_75_plus": 165689,
            "tax_year": tax_year
        }
        
        medical_credits = {
            "main_member": 347,
            "additional_member": 347,
            "tax_year": tax_year
        }
        
        self.success_count += 1
        logger.info(f"Using manual tax data for {tax_year} (2024-2025 values)")
        
        return {
            "tax_year": tax_year,
            "brackets": brackets,
            "rebates": rebates,
            "thresholds": thresholds,
            "medical_credits": medical_credits
        }
    
    async def save_to_database(self, db: Session, data: Dict[str, Any], force: bool = False) -> bool:
        """Save tax data to the database."""
        tax_year = data["tax_year"]
        
        # Check if data already exists
        if not force:
            existing = db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).first()
            if existing:
                logger.info(f"Tax data for {tax_year} already exists. Use --force to override.")
                return False
        
        # Clear existing data if force is True
        if force:
            logger.info(f"Clearing existing tax data for {tax_year}")
            db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).delete()
            db.query(TaxRebate).filter(TaxRebate.tax_year == tax_year).delete()
            db.query(TaxThreshold).filter(TaxThreshold.tax_year == tax_year).delete()
            db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == tax_year).delete()
        
        try:
            # Add tax brackets
            for bracket in data["brackets"]:
                db.add(TaxBracket(**bracket))
            
            # Add tax rebate
            db.add(TaxRebate(**data["rebates"]))
            
            # Add tax threshold
            db.add(TaxThreshold(**data["thresholds"]))
            
            # Add medical tax credit
            db.add(MedicalTaxCredit(**data["medical_credits"]))
            
            # Commit changes
            db.commit()
            logger.info(f"Successfully saved {tax_year} tax data to database")
            return True
        except Exception as e:
            logger.error(f"Error saving tax data to database: {e}")
            db.rollback()
            return False
    
    async def fetch_and_save_tax_data(self, db: Session, tax_year: str, force: bool = False, manual: bool = False) -> bool:
        """
        Main function to fetch tax data and save it to the database.
        Uses multiple approaches with fallbacks.
        """
        logger.info(f"Starting tax data fetch for {tax_year}")
        
        if manual:
            # Skip scraping and use manual data
            data = await self.get_manual_tax_data(tax_year)
            return await self.save_to_database(db, data, force)
        
        # Try multiple approaches
        
        # Approach 1: Current page
        data = await self.fetch_tax_data_from_current_page(tax_year)
        if data and data["brackets"]:
            return await self.save_to_database(db, data, force)
        
        # Approach 2: Archive page
        data = await self.fetch_tax_data_from_archive(tax_year)
        if data and data["brackets"]:
            return await self.save_to_database(db, data, force)
        
        # Approach 3: Manual fallback
        logger.warning(f"All scraping approaches failed for {tax_year}, using manual data")
        data = await self.get_manual_tax_data(tax_year)
        return await self.save_to_database(db, data, force)

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
    file_handler = logging.FileHandler(f"tax_data_{tax_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.info(f"Starting tax data retrieval for {tax_year}")
    logger.info(f"Force override: {args.force}")
    logger.info(f"Manual data: {args.manual}")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create the fetcher and run it
        fetcher = TaxDataFetcher()
        result = await fetcher.fetch_and_save_tax_data(db, tax_year, args.force, args.manual)
        
        if result:
            logger.info(f"Successfully processed tax data for {tax_year}")
            print(f"\n✅ SUCCESS: Tax data for {tax_year} has been saved to the database")
        else:
            logger.warning(f"No new tax data saved for {tax_year}")
            print(f"\n⚠️ WARNING: No new tax data was saved for {tax_year}")
        
        # Print summary
        print(f"\nSummary:")
        print(f"- Successful operations: {fetcher.success_count}")
        print(f"- Errors encountered: {fetcher.error_count}")
        print(f"- Log file: tax_data_{tax_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        print(f"\n❌ ERROR: Failed to process tax data - {str(e)}")
    finally:
        db.close()
        logger.info("Database session closed")

if __name__ == "__main__":
    asyncio.run(main())