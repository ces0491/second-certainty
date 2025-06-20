# app/core/scraping/tax_repository.py
import logging
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.tax_models import MedicalTaxCredit, TaxBracket, TaxRebate, TaxThreshold

logger = logging.getLogger(__name__)


class TaxDataRepository:
    """Repository for tax data database operations."""

    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def check_tax_data_exists(self, tax_year: str) -> bool:
        """
        Check if tax data exists for a specific tax year.
        Args:
            tax_year: The tax year to check
        Returns:
            True if tax data exists, False otherwise
        """
        existing = self.db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).first()
        return existing is not None

    def clear_tax_data(self, tax_year: str) -> None:
        """
        Clear all tax data for a specific tax year.
        Args:
            tax_year: The tax year to clear
        """
        logger.info(f"Clearing existing tax data for {tax_year}")
        self.db.query(TaxBracket).filter(TaxBracket.tax_year == tax_year).delete()
        self.db.query(TaxRebate).filter(TaxRebate.tax_year == tax_year).delete()
        self.db.query(TaxThreshold).filter(TaxThreshold.tax_year == tax_year).delete()
        self.db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == tax_year).delete()

    def save_tax_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Save tax data to the database.
        Args:
            data: Dictionary containing tax data
        Returns:
            Tuple of (success, error_message)
        """
        tax_year = data["tax_year"]
        logger.info(f"Saving tax data for {tax_year} to the database")
        try:
            # Add tax brackets
            for bracket in data["brackets"]:
                self.db.add(TaxBracket(**bracket))
            # Add tax rebate
            self.db.add(TaxRebate(**data["rebates"]))
            # Add tax threshold
            self.db.add(TaxThreshold(**data["thresholds"]))
            # Add medical tax credit
            self.db.add(MedicalTaxCredit(**data["medical_credits"]))
            # Commit changes
            self.db.commit()
            logger.info(f"Successfully saved {tax_year} tax data to database")
            return True, None
        except Exception as e:
            self.db.rollback()
            error_message = f"Error saving tax data to database: {e}"
            logger.error(error_message)
            return False, error_message

    def get_previous_tax_year_data(self, previous_tax_year: str, target_tax_year: str) -> Optional[Dict[str, Any]]:
        """
        Get tax data from a previous tax year and update for a new tax year.
        Args:
            previous_tax_year: The previous tax year to get data from
            target_tax_year: The target tax year to update data for
        Returns:
            Dictionary containing tax data for the target tax year, or None if not found
        """
        # Get previous year tax brackets
        brackets = self.db.query(TaxBracket).filter(TaxBracket.tax_year == previous_tax_year).all()
        if not brackets:
            logger.warning(f"No tax brackets found for previous year {previous_tax_year}")
            return None
        # Get previous year rebate
        rebate = self.db.query(TaxRebate).filter(TaxRebate.tax_year == previous_tax_year).first()
        # Get previous year threshold
        threshold = self.db.query(TaxThreshold).filter(TaxThreshold.tax_year == previous_tax_year).first()
        # Get previous year medical credit
        medical = self.db.query(MedicalTaxCredit).filter(MedicalTaxCredit.tax_year == previous_tax_year).first()
        if not rebate or not threshold or not medical:
            logger.warning(f"Incomplete tax data for previous year {previous_tax_year}")
            return None
        # Create updated data for target tax year
        updated_brackets = [
            {
                "lower_limit": bracket.lower_limit,
                "upper_limit": bracket.upper_limit,
                "rate": bracket.rate,
                "base_amount": bracket.base_amount,
                "tax_year": target_tax_year,
            }
            for bracket in brackets
        ]
        updated_rebates = {
            "primary": rebate.primary,
            "secondary": rebate.secondary,
            "tertiary": rebate.tertiary,
            "tax_year": target_tax_year,
        }
        updated_thresholds = {
            "below_65": threshold.below_65,
            "age_65_to_74": threshold.age_65_to_74,
            "age_75_plus": threshold.age_75_plus,
            "tax_year": target_tax_year,
        }
        updated_medical_credits = {
            "main_member": medical.main_member,
            "additional_member": medical.additional_member,
            "tax_year": target_tax_year,
        }
        return {
            "tax_year": target_tax_year,
            "brackets": updated_brackets,
            "rebates": updated_rebates,
            "thresholds": updated_thresholds,
            "medical_credits": updated_medical_credits,
        }
