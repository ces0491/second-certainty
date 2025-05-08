# app/core/data_scraper.py
import httpx
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re
from typing import Dict, List, Tuple, Any, Optional
from sqlalchemy.orm import Session

from app.models.tax_models import TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit
from app.utils.tax_utils import get_tax_year

logger = logging.getLogger(__name__)

class SARSDataScraper:
    """
    Scraper for South African Revenue Service tax tables and rates.
    Retrieves personal income tax tables, rebates, thresholds, and more.
    """
    
    SARS_BASE_URL = "https://www.sars.gov.za"
    TAX_RATES_URL = f"{SARS_BASE_URL}/rates/income-tax/rates-of-tax-for-individuals"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
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
    
    async def extract_tax_brackets(self, html_content: str, tax_year: str) -> List[Dict[str, Any]]:
        """
        Extract personal income tax brackets from SARS website.
        
        Returns a list of dictionaries containing:
        - lower_limit: The lower income bound for the bracket
        - upper_limit: The upper income bound for the bracket (None for the highest bracket)
        - rate: The tax rate for this bracket (as a decimal)
        - base_amount: The base tax amount for this bracket
        - tax_year: The tax year these brackets apply to
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        tax_brackets = []
        
        # Find the tax brackets table
        # This pattern might need adjustment based on the actual SARS website structure
        tables = soup.find_all('table')
        brackets_table = None
        
        for table in tables:
            # Look for tables with headers that match tax bracket patterns
            headers = table.find_all('th')
            header_text = " ".join([h.text.strip() for h in headers])
            if "Taxable income" in header_text and "Rate of tax" in header_text:
                brackets_table = table
                break
        
        if not brackets_table:
            logger.error("Could not find tax brackets table")
            return []
        
        # Extract rows from the table
        rows = brackets_table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                # Parse the taxable income range
                income_range = cells[0].text.strip()
                rate_text = cells[1].text.strip()
                
                # Extract lower and upper bounds using regex
                income_match = re.search(r'R\s*([\d\s]+)\s*–\s*R\s*([\d\s]+)', income_range)
                if income_match:
                    lower_limit = int(income_match.group(1).replace(" ", ""))
                    upper_limit = int(income_match.group(2).replace(" ", ""))
                else:
                    # Check if it's the highest bracket (e.g., "R1 817 001 and above")
                    exceed_match = re.search(r'R\s*([\d\s]+)\s*and above', income_range)
                    if exceed_match:
                        lower_limit = int(exceed_match.group(1).replace(" ", ""))
                        upper_limit = None
                    else:
                        continue  # Skip if we can't parse the range
                
                # Extract rate and base amount
                # Format typically like "18% of taxable income" or "R165 750 + 36% of taxable income above R617 001"
                base_amount = 0
                rate = 0
                
                if "+" in rate_text:
                    # Extract the base amount for higher brackets
                    base_match = re.search(r'R\s*([\d\s]+)', rate_text)
                    if base_match:
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
    
    async def extract_tax_rebates(self, html_content: str, tax_year: str) -> Dict[str, float]:
        """
        Extract tax rebates from SARS website.
        
        Returns a dictionary with rebate types and amounts:
        - primary: Primary rebate for all individuals
        - secondary: Additional rebate for individuals 65 and older
        - tertiary: Additional rebate for individuals 75 and older
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        rebates = {
            "primary": 0,
            "secondary": 0,
            "tertiary": 0,
            "tax_year": tax_year
        }
        
        # Look for rebate information in tables or specific sections
        rebate_section = None
        for section in soup.find_all(['div', 'section', 'table']):
            if "rebate" in section.text.lower() and "R" in section.text:
                rebate_section = section
                break
        
        if rebate_section:
            text = rebate_section.text
            
            # Find primary rebate
            primary_match = re.search(r'primary\s+rebate.*?R\s*([\d\s]+)', text, re.I)
            if primary_match:
                rebates["primary"] = int(primary_match.group(1).replace(" ", ""))
            
            # Find secondary rebate
            secondary_match = re.search(r'secondary\s+rebate.*?R\s*([\d\s]+)', text, re.I)
            if secondary_match:
                rebates["secondary"] = int(secondary_match.group(1).replace(" ", ""))
            
            # Find tertiary rebate
            tertiary_match = re.search(r'tertiary\s+rebate.*?R\s*([\d\s]+)', text, re.I)
            if tertiary_match:
                rebates["tertiary"] = int(tertiary_match.group(1).replace(" ", ""))
        
        return rebates
    
    async def extract_tax_thresholds(self, html_content: str, tax_year: str) -> Dict[str, int]:
        """
        Extract tax thresholds from SARS website.
        
        Returns a dictionary with age groups and thresholds:
        - below_65: Threshold for individuals under 65
        - age_65_to_74: Threshold for individuals 65-74
        - age_75_plus: Threshold for individuals 75 and older
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        thresholds = {
            "below_65": 0,
            "age_65_to_74": 0,
            "age_75_plus": 0,
            "tax_year": tax_year
        }
        
        # Look for threshold information
        threshold_section = None
        for section in soup.find_all(['div', 'section', 'table']):
            if "threshold" in section.text.lower() and "R" in section.text:
                threshold_section = section
                break
        
        if threshold_section:
            text = threshold_section.text
            
            # Parse thresholds by age group
            below_65_match = re.search(r'below.*?65.*?R\s*([\d\s]+)', text, re.I)
            if below_65_match:
                thresholds["below_65"] = int(below_65_match.group(1).replace(" ", ""))
            
            age_65_match = re.search(r'age.*?65.*?74.*?R\s*([\d\s]+)', text, re.I)
            if age_65_match:
                thresholds["age_65_to_74"] = int(age_65_match.group(1).replace(" ", ""))
            
            age_75_match = re.search(r'age.*?75.*?R\s*([\d\s]+)', text, re.I)
            if age_75_match:
                thresholds["age_75_plus"] = int(age_75_match.group(1).replace(" ", ""))
        
        return thresholds
    
    async def extract_medical_tax_credits(self, html_content: str, tax_year: str) -> Dict[str, float]:
        """
        Extract medical tax credits from SARS website.
        
        Returns a dictionary with:
        - main_member: Credit for the main member
        - additional_member: Credit for each additional member
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        credits = {
            "main_member": 0,
            "additional_member": 0,
            "tax_year": tax_year
        }
        
        # Find medical tax credit information
        medical_section = None
        for section in soup.find_all(['div', 'section', 'table']):
            if "medical" in section.text.lower() and "scheme" in section.text.lower() and "R" in section.text:
                medical_section = section
                break
        
        if medical_section:
            text = medical_section.text
            
            # Parse credits
            main_match = re.search(r'main\s+member.*?R\s*([\d\s\.]+)', text, re.I)
            if main_match:
                credits["main_member"] = float(main_match.group(1).replace(" ", ""))
            
            additional_match = re.search(r'additional.*?member.*?R\s*([\d\s\.]+)', text, re.I)
            if additional_match:
                credits["additional_member"] = float(additional_match.group(1).replace(" ", ""))
        
        return credits
    
    async def update_tax_data(self, db: Session) -> Dict[str, Any]:
        """Scrape and update all tax-related data for the current tax year."""
        tax_year = get_tax_year()
        
        # Fetch SARS tax rates page
        html_content = await self.fetch_page(self.TAX_RATES_URL)
        
        # Extract different tax components
        brackets = await self.extract_tax_brackets(html_content, tax_year)
        rebates = await self.extract_tax_rebates(html_content, tax_year)
        thresholds = await self.extract_tax_thresholds(html_content, tax_year)
        medical_credits = await self.extract_medical_tax_credits(html_content, tax_year)
        
        # Update database with new data
        # Clear existing data for this tax year
        db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).delete()
        db.query(TaxRebate).filter(TaxRebate.tax_year == tax_year).delete()
        db.query(TaxThreshold).filter(TaxThreshold.tax_year == tax_year).delete()
        db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == tax_year).delete()
        
        # Add new tax brackets
        for bracket in brackets:
            db.add(TaxBracket(**bracket))
        
        # Add new tax rebates
        db.add(TaxRebate(**rebates))
        
        # Add new tax thresholds
        db.add(TaxThreshold(**thresholds))
        
        # Add new medical tax credits
        db.add(MedicalTaxCredit(**medical_credits))
        
        # Commit changes
        db.commit()
        
        return {
            "tax_year": tax_year,
            "brackets": brackets,
            "rebates": rebates,
            "thresholds": thresholds,
            "medical_credits": medical_credits
        }