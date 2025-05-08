# app/core/tax_calculator.py
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple, Any
import math
from datetime import datetime

from app.models.tax_models import (
    TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit,
    UserProfile, IncomeSource, UserExpense, TaxCalculation
)
from app.utils.tax_utils import get_tax_year, calculate_age

class TaxCalculator:
    """
    Handles all South African personal income tax calculations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_tax_brackets(self, tax_year: str) -> List[Dict[str, Any]]:
        """Get tax brackets for the specified tax year."""
        brackets = self.db.query(TaxBracket).filter(
            TaxBracket.tax_year == tax_year
        ).order_by(TaxBracket.lower_limit).all()
        
        return [
            {
                "lower_limit": bracket.lower_limit,
                "upper_limit": bracket.upper_limit,
                "rate": bracket.rate,
                "base_amount": bracket.base_amount
            }
            for bracket in brackets
        ]
    
    def get_tax_rebates(self, tax_year: str) -> Dict[str, float]:
        """Get tax rebates for the specified tax year."""
        rebate = self.db.query(TaxRebate).filter(
            TaxRebate.tax_year == tax_year
        ).first()
        
        if not rebate:
            return {"primary": 0, "secondary": 0, "tertiary": 0}
        
        return {
            "primary": rebate.primary,
            "secondary": rebate.secondary,
            "tertiary": rebate.tertiary
        }
    
    def get_tax_thresholds(self, tax_year: str) -> Dict[str, int]:
        """Get tax thresholds for the specified tax year."""
        threshold = self.db.query(TaxThreshold).filter(
            TaxThreshold.tax_year == tax_year
        ).first()
        
        if not threshold:
            return {"below_65": 0, "age_65_to_74": 0, "age_75_plus": 0}
        
        return {
            "below_65": threshold.below_65,
            "age_65_to_74": threshold.age_65_to_74,
            "age_75_plus": threshold.age_75_plus
        }
    
    def get_medical_tax_credits(self, tax_year: str) -> Dict[str, float]:
        """Get medical tax credits for the specified tax year."""
        credit = self.db.query(MedicalTaxCredit).filter(
            MedicalTaxCredit.tax_year == tax_year
        ).first()
        
        if not credit:
            return {"main_member": 0, "additional_member": 0}
        
        return {
            "main_member": credit.main_member,
            "additional_member": credit.additional_member
        }
    
    def calculate_income_tax(self, taxable_income: float, tax_year: str) -> float:
        """
        Calculate income tax based on taxable income and tax brackets.
        Does not include rebates or credits.
        """
        brackets = self.get_tax_brackets(tax_year)
        
        if not brackets:
            raise ValueError(f"No tax brackets found for tax year {tax_year}")
        
        # Find the applicable bracket
        applicable_bracket = None
        for bracket in brackets:
            if taxable_income >= bracket["lower_limit"] and (
                bracket["upper_limit"] is None or taxable_income <= bracket["upper_limit"]
            ):
                applicable_bracket = bracket
                break
        
        if not applicable_bracket:
            raise ValueError(f"Could not determine tax bracket for income R{taxable_income}")
        
        # Calculate tax
        base_amount = applicable_bracket["base_amount"]
        rate = applicable_bracket["rate"]
        lower_limit = applicable_bracket["lower_limit"]
        
        tax = base_amount + (rate * (taxable_income - lower_limit))
        return tax
    
    def calculate_rebate(self, age: int, tax_year: str) -> float:
        """Calculate total rebates based on age."""
        rebates = self.get_tax_rebates(tax_year)
        
        total_rebate = rebates["primary"]
        
        if age >= 65:
            total_rebate += rebates["secondary"]
        
        if age >= 75:
            total_rebate += rebates["tertiary"]
        
        return total_rebate
    
    def calculate_medical_credit(self, main_members: int, additional_members: int, tax_year: str) -> float:
        """Calculate medical scheme fee tax credits."""
        credits = self.get_medical_tax_credits(tax_year)
        
        total_credit = (credits["main_member"] * main_members) + (credits["additional_member"] * additional_members)
        return total_credit
    
    def calculate_tax_threshold(self, age: int, tax_year: str) -> int:
        """Get the tax threshold based on age."""
        thresholds = self.get_tax_thresholds(tax_year)
        
        if age >= 75:
            return thresholds["age_75_plus"]
        elif age >= 65:
            return thresholds["age_65_to_74"]
        else:
            return thresholds["below_65"]
    
    def calculate_deductible_expenses(self, user_id: int, tax_year: str) -> float:
        """Calculate total deductible expenses for a user."""
        expenses = self.db.query(UserExpense).filter(
            UserExpense.user_id == user_id,
            UserExpense.tax_year == tax_year
        ).all()
        
        total_deductible = 0
        for expense in expenses:
            # Additional logic can be added here to handle specific expense types
            # and their respective limits or rules
            total_deductible += expense.amount
        
        return total_deductible
    
    def calculate_tax_liability(
        self, 
        user_id: int, 
        tax_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate complete tax liability for a user.
        
        Returns a dictionary with:
        - gross_income: Total income before deductions
        - taxable_income: Income after deductions
        - tax_before_rebates: Tax calculated on taxable income
        - rebates: Tax rebates applicable
        - medical_credits: Medical scheme fee tax credits
        - final_tax: Tax after rebates and credits
        - effective_tax_rate: Final tax as a percentage of taxable income
        - monthly_tax_rate: Effective monthly tax rate
        """
        if tax_year is None:
            tax_year = get_tax_year()
        
        # Get user profile
        user = self.db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Calculate age
        age = calculate_age(user.date_of_birth)
        
        # Get income sources
        income_sources = self.db.query(IncomeSource).filter(
            IncomeSource.user_id == user_id,
            IncomeSource.tax_year == tax_year
        ).all()
        
        # Calculate gross income
        gross_income = sum(source.annual_amount for source in income_sources)
        
        # Calculate deductible expenses
        deductible_expenses = self.calculate_deductible_expenses(user_id, tax_year)
        
        # Calculate taxable income
        taxable_income = gross_income - deductible_expenses
        if taxable_income < 0:
            taxable_income = 0
        
        # Check if income is above threshold
        threshold = self.calculate_tax_threshold(age, tax_year)
        
        if taxable_income <= threshold:
            # Below tax threshold, no tax
            return {
                "gross_income": gross_income,
                "taxable_income": taxable_income,
                "tax_before_rebates": 0,
                "rebates": 0,
                "medical_credits": 0,
                "final_tax": 0,
                "effective_tax_rate": 0,
                "monthly_tax_rate": 0
            }
        
        # Calculate tax before rebates
        tax_before_rebates = self.calculate_income_tax(taxable_income, tax_year)
        
        # Calculate rebates
        rebates = self.calculate_rebate(age, tax_year)
        
        # Calculate medical credits (assuming user is main member with no dependents)
        # This would need to be expanded with actual data
        medical_credits = self.calculate_medical_credit(1, 0, tax_year)
        
        # Calculate final tax
        final_tax = max(0, tax_before_rebates - rebates - medical_credits)
        
        # Calculate effective tax rate
        effective_tax_rate = final_tax / taxable_income if taxable_income > 0 else 0
        
        # Calculate monthly tax rate
        monthly_tax_rate = final_tax / (12 * gross_income) if gross_income > 0 else 0
        
        # Store calculation
        tax_calc = TaxCalculation(
            user_id=user_id,
            tax_year=tax_year,
            gross_income=gross_income,
            taxable_income=taxable_income,
            tax_liability=tax_before_rebates,
            tax_credits=rebates + medical_credits,
            final_tax=final_tax,
            effective_tax_rate=effective_tax_rate,
            monthly_tax_rate=monthly_tax_rate
        )
        self.db.add(tax_calc)
        self.db.commit()
        
        return {
            "gross_income": gross_income,
            "taxable_income": taxable_income,
            "tax_before_rebates": tax_before_rebates,
            "rebates": rebates,
            "medical_credits": medical_credits,
            "final_tax": final_tax,
            "effective_tax_rate": effective_tax_rate,
            "monthly_tax_rate": monthly_tax_rate
        }
    
    def calculate_provisional_tax(
        self, 
        user_id: int, 
        tax_year: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate provisional tax payments for provisional taxpayers.
        
        Returns a dictionary with:
        - annual_tax: Total annual tax liability
        - first_payment: First provisional payment (due August)
        - second_payment: Second provisional payment (due February)
        - final_payment: Final payment (due with tax return)
        """
        if tax_year is None:
            tax_year = get_tax_year()
        
        # Get user profile
        user = self.db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if user is a provisional taxpayer
        if not user.is_provisional_taxpayer:
            raise ValueError(f"User with ID {user_id} is not a provisional taxpayer")
        
        # Calculate total tax liability
        tax_liability = self.calculate_tax_liability(user_id, tax_year)
        annual_tax = tax_liability["final_tax"]
        
        # Calculate provisional payments
        first_payment = annual_tax * 0.5
        second_payment = annual_tax * 0.5
        final_payment = 0  # Assuming accurate estimates; otherwise, this would be the difference
        
        return {
            "annual_tax": annual_tax,
            "first_payment": first_payment,
            "second_payment": second_payment,
            "final_payment": final_payment
        }