# app/core/scraping/tax_provider.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TaxDataProvider:
    """Provider for manual tax data when scraping fails."""
    
    @staticmethod
    def get_manual_tax_data(tax_year: str) -> Dict[str, Any]:
        """
        Provide manual tax data for a specific tax year.
        
        Args:
            tax_year: The tax year to provide data for
            
        Returns:
            Dictionary containing tax data
        """
        logger.info(f"Providing manual tax data for {tax_year}")
        
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
        
        logger.info(f"Using manual tax data for {tax_year} (2024-2025 values)")
        
        return {
            "tax_year": tax_year,
            "brackets": brackets,
            "rebates": rebates,
            "thresholds": thresholds,
            "medical_credits": medical_credits
        }