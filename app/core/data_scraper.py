# app/core/data_scraper.py
import httpx
from bs4 import BeautifulSoup
import logging
import re
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy.orm import Session

from app.models.tax_models import TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit
from app.utils.tax_utils import get_tax_year

logger = logging.getLogger(__name__)

class SARSDataScraper:
    """
    Enhanced scraper for South African Revenue Service tax tables and rates.
    Handles current and historical tax data with support for 'No changes' scenarios.
    """
    
    SARS_BASE_URL = "https://www.sars.gov.za"
    TAX_RATES_URL = f"{SARS_BASE_URL}/tax-rates/income-tax/rates-of-tax-for-individuals/"
    ARCHIVE_URL = f"{SARS_BASE_URL}/tax-rates/archive-tax-rates/"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        # Cache to store tax data by year
        self.tax_data_cache = {}
    
    async def fetch_page(self, url: str) -> str:
        """Fetch HTML content from a URL."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    async def extract_tax_year_sections(self, html_content: str) -> Dict[str, Dict]:
        """
        Extract different tax year sections from the main page.
        Returns a dictionary mapping tax years to their content blocks.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        tax_years = {}
        
        # Find all tax year headings (they're typically h2 elements with the year in them)
        year_headings = soup.find_all(['h2', 'h3'], string=re.compile(r'\d{4} tax year'))
        
        for heading in year_headings:
            # Extract the tax year from the heading text
            year_match = re.search(r'(\d{4}) tax year', heading.text)
            if not year_match:
                continue
                
            end_year = year_match.group(1)
            tax_year = f"{int(end_year)-1}-{end_year}"
            
            # Check if this section mentions "No changes"
            section_content = ""
            current_element = heading.next_sibling
            
            # Collect content until next heading or end of relevant section
            while current_element and not (current_element.name in ['h2', 'h3'] and re.search(r'\d{4} tax year', current_element.text)):
                if hasattr(current_element, 'text'):
                    section_content += current_element.text
                current_element = current_element.next_sibling
            
            has_changes = True
            
            # Check for "No changes" text
            if re.search(r'[nN]o changes', section_content):
                has_changes = False
                logger.info(f"Tax year {tax_year} has no changes from previous year")
            
            # Find any tables in this section
            tables = []
            current_element = heading.next_sibling
            while current_element and not (current_element.name in ['h2', 'h3'] and re.search(r'\d{4} tax year', current_element.text)):
                if current_element.name == 'table':
                    tables.append(current_element)
                elif hasattr(current_element, 'find_all'):
                    tables.extend(current_element.find_all('table'))
                current_element = current_element.next_sibling
            
            tax_years[tax_year] = {
                'has_changes': has_changes,
                'tables': tables,
                'content': section_content
            }
        
        return tax_years
    
    async def extract_tax_brackets(self, section_data: Dict, tax_year: str) -> List[Dict[str, Any]]:
        """
        Extract tax brackets from a section.
        If the section has no changes, it will return an empty list.
        """
        if not section_data['has_changes']:
            return []
            
        tables = section_data['tables']
        tax_brackets = []
        
        # Find the tax brackets table
        brackets_table = None
        for table in tables:
            headers = table.find_all('th')
            header_text = " ".join([h.text.strip() for h in headers])
            if "Taxable income" in header_text and "Rates of tax" in header_text:
                brackets_table = table
                break
        
        if not brackets_table:
            logger.error(f"Could not find tax brackets table for {tax_year}")
            return []
        
        # Extract rows from the table
        rows = brackets_table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                # Parse the taxable income range
                income_range = cells[0].text.strip()
                rate_text = cells[1].text.strip()
                
                # Extract lower and upper bounds
                income_match = re.search(r'(\d[\d\s]*)\s*[–-]\s*(\d[\d\s]*)', income_range)
                if income_match:
                    lower_limit = int(income_match.group(1).replace(" ", ""))
                    upper_limit = int(income_match.group(2).replace(" ", ""))
                else:
                    # Check if it's the highest bracket (e.g., "1 817 001 and above")
                    exceed_match = re.search(r'(\d[\d\s]*)\s*and above', income_range)
                    if exceed_match:
                        lower_limit = int(exceed_match.group(1).replace(" ", ""))
                        upper_limit = None
                    else:
                        continue  # Skip if we can't parse the range
                
                # Extract base amount and rate
                base_amount = 0
                rate = 0
                
                # Format: "R165 750 + 36% of taxable income above R617 001"
                base_match = re.search(r'(\d[\d\s]*)', rate_text)
                if base_match and "+" in rate_text:
                    base_amount = int(base_match.group(1).replace(" ", ""))
                
                # Extract the rate percentage
                rate_match = re.search(r'(\d+)%', rate_text)
                if rate_match:
                    rate = int(rate_match.group(1)) / 100
                
                tax_brackets.append({
                    "lower_limit": lower_limit,
                    "upper_limit": upper_limit,
                    "rate": rate,
                    "base_amount": base_amount,
                    "tax_year": tax_year
                })
        
        return tax_brackets
    
    async def extract_tax_rebates(self, section_data: Dict, tax_year: str) -> Dict[str, float]:
        """Extract tax rebates from a section."""
        if not section_data['has_changes']:
            return {}
        
        content = section_data['content']
        rebates = {
            "primary": 0,
            "secondary": 0,
            "tertiary": 0,
            "tax_year": tax_year
        }
        
        # Look for rebate information
        primary_match = re.search(r'[Pp]rimary\s+rebate.*?R\s*([\d\s]+)', content)
        if primary_match:
            rebates["primary"] = int(primary_match.group(1).replace(" ", ""))
        
        secondary_match = re.search(r'[Ss]econdary\s+rebate.*?R\s*([\d\s]+)', content)
        if secondary_match:
            rebates["secondary"] = int(secondary_match.group(1).replace(" ", ""))
        
        tertiary_match = re.search(r'[Tt]ertiary\s+rebate.*?R\s*([\d\s]+)', content)
        if tertiary_match:
            rebates["tertiary"] = int(tertiary_match.group(1).replace(" ", ""))
        
        return rebates
    
    async def extract_tax_thresholds(self, section_data: Dict, tax_year: str) -> Dict[str, int]:
        """Extract tax thresholds from a section."""
        if not section_data['has_changes']:
            return {}
        
        content = section_data['content']
        thresholds = {
            "below_65": 0,
            "age_65_to_74": 0,
            "age_75_plus": 0,
            "tax_year": tax_year
        }
        
        # Look for threshold information
        below_65_match = re.search(r'[Bb]elow.*?65.*?R\s*([\d\s]+)', content)
        if below_65_match:
            thresholds["below_65"] = int(below_65_match.group(1).replace(" ", ""))
        
        age_65_match = re.search(r'[Aa]ge.*?65.*?74.*?R\s*([\d\s]+)', content)
        if age_65_match:
            thresholds["age_65_to_74"] = int(age_65_match.group(1).replace(" ", ""))
        
        age_75_match = re.search(r'[Aa]ge.*?75.*?R\s*([\d\s]+)', content)
        if age_75_match:
            thresholds["age_75_plus"] = int(age_75_match.group(1).replace(" ", ""))
        
        return thresholds
    
    async def extract_medical_tax_credits(self, section_data: Dict, tax_year: str) -> Dict[str, float]:
        """Extract medical tax credits from a section."""
        if not section_data['has_changes']:
            return {}
        
        content = section_data['content']
        credits = {
            "main_member": 0,
            "additional_member": 0,
            "tax_year": tax_year
        }
        
        # Look for medical credit information
        main_match = re.search(r'[Mm]ain\s+member.*?R\s*([\d\s\.]+)', content)
        if main_match:
            credits["main_member"] = float(main_match.group(1).replace(" ", ""))
        
        additional_match = re.search(r'[Aa]dditional.*?member.*?R\s*([\d\s\.]+)', content)
        if additional_match:
            credits["additional_member"] = float(additional_match.group(1).replace(" ", ""))
        
        return credits
    
    async def get_all_tax_years_data(self, db: Session, requested_tax_year: str = None) -> Dict[str, Any]:
        """
        Get tax data for all available years, handling "No changes" scenarios.
        
        Args:
            db: Database session
            requested_tax_year: The specific tax year to focus on (optional)
        
        Returns:
            Dictionary mapping tax years to their complete tax data
        """
        if not requested_tax_year:
            requested_tax_year = get_tax_year()
        
        # Fetch main tax page
        html_content = await self.fetch_page(self.TAX_RATES_URL)
        tax_year_sections = await self.extract_tax_year_sections(html_content)
        
        # Initialize result dictionary
        all_tax_data = {}
        
        # Process tax years in reverse chronological order
        sorted_years = sorted(tax_year_sections.keys(), key=lambda x: int(x.split('-')[1]), reverse=True)
        
        # First pass: Extract data for years with changes
        for tax_year in sorted_years:
            section_data = tax_year_sections[tax_year]
            
            if section_data['has_changes']:
                # Extract data for this year
                brackets = await self.extract_tax_brackets(section_data, tax_year)
                rebates = await self.extract_tax_rebates(section_data, tax_year)
                thresholds = await self.extract_tax_thresholds(section_data, tax_year)
                medical_credits = await self.extract_medical_tax_credits(section_data, tax_year)
                
                all_tax_data[tax_year] = {
                    'brackets': brackets,
                    'rebates': rebates,
                    'thresholds': thresholds,
                    'medical_credits': medical_credits
                }
        
        # Second pass: Propagate data for years with no changes
        current_data = None
        for tax_year in sorted_years:
            if tax_year in all_tax_data:
                # This year has its own data
                current_data = all_tax_data[tax_year]
            elif current_data:
                # This year has no changes, use data from previous year
                section_data = tax_year_sections[tax_year]
                if not section_data['has_changes']:
                    # Copy data from the previous year but update the tax_year field
                    year_data = {
                        'brackets': [
                            {**bracket, 'tax_year': tax_year}
                            for bracket in current_data['brackets']
                        ],
                        'rebates': {**current_data['rebates'], 'tax_year': tax_year},
                        'thresholds': {**current_data['thresholds'], 'tax_year': tax_year},
                        'medical_credits': {**current_data['medical_credits'], 'tax_year': tax_year}
                    }
                    all_tax_data[tax_year] = year_data
        
        # If we need archive data, fetch it
        if requested_tax_year not in all_tax_data:
            archive_data = await self.get_archived_tax_data(db, requested_tax_year)
            if archive_data:
                all_tax_data[requested_tax_year] = archive_data
        
        return all_tax_data
    
    async def get_archived_tax_data(self, db: Session, tax_year: str) -> Dict[str, Any]:
        """
        Fetch and extract tax data from the archive page.
        
        Args:
            db: Database session
            tax_year: The specific tax year to fetch from archives
        
        Returns:
            Tax data for the requested year if found
        """
        try:
            # Fetch archive page
            html_content = await self.fetch_page(self.ARCHIVE_URL)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for a link to the specific tax year
            year_end = tax_year.split('-')[1]
            archive_link = None
            
            # Find links that might contain the tax year
            for link in soup.find_all('a'):
                if year_end in link.text and ('income tax' in link.text.lower() or 'individuals' in link.text.lower()):
                    archive_link = link.get('href')
                    if not archive_link.startswith('http'):
                        archive_link = f"{self.SARS_BASE_URL}{archive_link}"
                    break
            
            if not archive_link:
                logger.error(f"Could not find archive link for tax year {tax_year}")
                return None
            
            # Fetch the specific archive page
            archive_content = await self.fetch_page(archive_link)
            
            # Create a section data structure to use with existing extraction methods
            section_data = {
                'has_changes': True,
                'content': archive_content,
                'tables': BeautifulSoup(archive_content, 'html.parser').find_all('table')
            }
            
            # Extract data
            brackets = await self.extract_tax_brackets(section_data, tax_year)
            rebates = await self.extract_tax_rebates(section_data, tax_year)
            thresholds = await self.extract_tax_thresholds(section_data, tax_year)
            medical_credits = await self.extract_medical_tax_credits(section_data, tax_year)
            
            return {
                'brackets': brackets,
                'rebates': rebates,
                'thresholds': thresholds,
                'medical_credits': medical_credits
            }
            
        except Exception as e:
            logger.error(f"Error fetching archived tax data for {tax_year}: {e}")
            return None
    
    async def update_tax_data(self, db: Session, tax_year: str = None) -> Dict[str, Any]:
        """
        Update tax data in the database for a specific tax year.
        Handles "No changes" scenarios by copying data from previous years.
        
        Args:
            db: Database session
            tax_year: The tax year to update (defaults to current tax year)
        
        Returns:
            Dictionary containing the updated tax data
        """
        if not tax_year:
            tax_year = get_tax_year()
        
        logger.info(f"Updating tax data for {tax_year}")
        
        try:
            # Get all tax year data
            all_tax_data = await self.get_all_tax_years_data(db, tax_year)
            
            if tax_year not in all_tax_data:
                raise ValueError(f"Could not find tax data for tax year {tax_year}")
            
            # Get data for requested tax year
            year_data = all_tax_data[tax_year]
            
            # Clear existing data for this tax year
            db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).delete()
            db.query(TaxRebate).filter(TaxRebate.tax_year == tax_year).delete()
            db.query(TaxThreshold).filter(TaxThreshold.tax_year == tax_year).delete()
            db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == tax_year).delete()
            
            # Add new tax brackets
            for bracket in year_data['brackets']:
                db.add(TaxBracket(**bracket))
            
            # Add new tax rebates
            db.add(TaxRebate(**year_data['rebates']))
            
            # Add new tax thresholds
            db.add(TaxThreshold(**year_data['thresholds']))
            
            # Add new medical tax credits
            db.add(MedicalTaxCredit(**year_data['medical_credits']))
            
            # Commit changes
            db.commit()
            
            return year_data
            
        except Exception as e:
            logger.error(f"Error updating tax data: {e}")
            db.rollback()
            raise