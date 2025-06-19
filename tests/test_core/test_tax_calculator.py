# tests/test_core/test_tax_calculator.py
import pytest
from unittest.mock import MagicMock
from datetime import date

from app.core.tax_calculator import TaxCalculator
from app.models.tax_models import (
    IncomeSource, UserExpense, UserProfile, TaxBracket, 
    TaxRebate, TaxThreshold, MedicalTaxCredit
)
from app.utils.tax_utils import get_tax_year


class TestTaxCalculator:
    """Test the TaxCalculator core functionality."""

    @pytest.fixture
    def calculator(self, test_db):
        """Create a TaxCalculator instance with test database."""
        return TaxCalculator(test_db)

    def test_get_tax_brackets(self, calculator, test_db, tax_data_setup):
        """Test retrieving tax brackets."""
        tax_year = tax_data_setup["tax_year"]
        brackets = calculator.get_tax_brackets(tax_year)
        
        assert len(brackets) == 7
        assert brackets[0]["lower_limit"] == 1
        assert brackets[0]["upper_limit"] == 237100
        assert brackets[0]["rate"] == 0.18
        assert brackets[0]["base_amount"] == 0
        
        # Test highest bracket (no upper limit)
        assert brackets[-1]["upper_limit"] is None
        assert brackets[-1]["rate"] == 0.45

    def test_get_tax_brackets_no_data(self, calculator):
        """Test retrieving tax brackets when no data exists."""
        brackets = calculator.get_tax_brackets("2099-2100")  # Non-existent year
        assert brackets == []

    def test_get_tax_rebates(self, calculator, tax_data_setup):
        """Test retrieving tax rebates."""
        tax_year = tax_data_setup["tax_year"]
        rebates = calculator.get_tax_rebates(tax_year)
        
        assert rebates["primary"] == 17235
        assert rebates["secondary"] == 9444
        assert rebates["tertiary"] == 3145

    def test_get_tax_thresholds(self, calculator, tax_data_setup):
        """Test retrieving tax thresholds."""
        tax_year = tax_data_setup["tax_year"]
        thresholds = calculator.get_tax_thresholds(tax_year)
        
        assert thresholds["below_65"] == 95750
        assert thresholds["age_65_to_74"] == 148217
        assert thresholds["age_75_plus"] == 165689

    def test_get_medical_tax_credits(self, calculator, tax_data_setup):
        """Test retrieving medical tax credits."""
        tax_year = tax_data_setup["tax_year"]
        credits = calculator.get_medical_tax_credits(tax_year)
        
        assert credits["main_member"] == 347
        assert credits["additional_member"] == 347

    def test_calculate_income_tax_first_bracket(self, calculator, tax_data_setup):
        """Test income tax calculation in first bracket (18%)."""
        tax_year = tax_data_setup["tax_year"]
        
        # Test income of R200,000 (within first bracket)
        tax = calculator.calculate_income_tax(200000, tax_year)
        expected = 200000 * 0.18  # 36,000
        assert abs(tax - expected) < 1.0

    def test_calculate_income_tax_second_bracket(self, calculator, tax_data_setup):
        """Test income tax calculation in second bracket (26%)."""
        tax_year = tax_data_setup["tax_year"]
        
        # Test income of R300,000 (in second bracket)
        tax = calculator.calculate_income_tax(300000, tax_year)
        # Base: R42,678 + 26% of (300,000 - 237,100) = 42,678 + 16,354 = 59,032
        expected = 42678 + (0.26 * (300000 - 237100))
        assert abs(tax - expected) < 1.0

    def test_calculate_income_tax_high_income(self, calculator, tax_data_setup):
        """Test income tax calculation for high income."""
        tax_year = tax_data_setup["tax_year"]
        
        # Test income of R2,000,000 (highest bracket - 45%)
        tax = calculator.calculate_income_tax(2000000, tax_year)
        # Base: R644,489 + 45% of (2,000,000 - 1,817,000) = 644,489 + 82,350 = 726,839
        expected = 644489 + (0.45 * (2000000 - 1817000))
        assert abs(tax - expected) < 1.0

    def test_calculate_income_tax_no_brackets(self, calculator):
        """Test income tax calculation when no brackets exist."""
        with pytest.raises(ValueError, match="No tax brackets found"):
            calculator.calculate_income_tax(100000, "2099-2100")

    def test_calculate_rebate_young_person(self, calculator, tax_data_setup):
        """Test rebate calculation for person under 65."""
        tax_year = tax_data_setup["tax_year"]
        rebate = calculator.calculate_rebate(30, tax_year)
        assert rebate == 17235  # Only primary rebate

    def test_calculate_rebate_senior(self, calculator, tax_data_setup):
        """Test rebate calculation for person 65-74."""
        tax_year = tax_data_setup["tax_year"]
        rebate = calculator.calculate_rebate(70, tax_year)
        assert rebate == 17235 + 9444  # Primary + secondary

    def test_calculate_rebate_elderly(self, calculator, tax_data_setup):
        """Test rebate calculation for person 75+."""
        tax_year = tax_data_setup["tax_year"]
        rebate = calculator.calculate_rebate(80, tax_year)
        assert rebate == 17235 + 9444 + 3145  # All three rebates

    def test_calculate_medical_credit(self, calculator, tax_data_setup):
        """Test medical credit calculation."""
        tax_year = tax_data_setup["tax_year"]
        
        # Single person (main member only)
        credit = calculator.calculate_medical_credit(1, 0, tax_year)
        assert credit == 347
        
        # Couple (main + 1 additional)
        credit = calculator.calculate_medical_credit(1, 1, tax_year)
        assert credit == 347 * 2
        
        # Family (main + 2 additional)
        credit = calculator.calculate_medical_credit(1, 2, tax_year)
        assert credit == 347 * 3

    def test_calculate_tax_threshold(self, calculator, tax_data_setup):
        """Test tax threshold calculation by age."""
        tax_year = tax_data_setup["tax_year"]
        
        # Under 65
        threshold = calculator.calculate_tax_threshold(30, tax_year)
        assert threshold == 95750
        
        # 65-74
        threshold = calculator.calculate_tax_threshold(70, tax_year)
        assert threshold == 148217
        
        # 75+
        threshold = calculator.calculate_tax_threshold(80, tax_year)
        assert threshold == 165689

    def test_calculate_deductible_expenses(self, calculator, test_user, test_db, expense_types_setup):
        """Test calculating total deductible expenses."""
        tax_year = get_tax_year()
        
        # Add some expenses
        expense1 = UserExpense(
            user_id=test_user.id,
            expense_type_id=1,
            description="Retirement contribution",
            amount=50000,
            tax_year=tax_year
        )
        expense2 = UserExpense(
            user_id=test_user.id,
            expense_type_id=2,
            description="Medical expenses",
            amount=15000,
            tax_year=tax_year
        )
        test_db.add(expense1)
        test_db.add(expense2)
        test_db.commit()
        
        total = calculator.calculate_deductible_expenses(test_user.id, tax_year)
        assert total == 65000

    def test_calculate_tax_liability_below_threshold(self, calculator, test_user, test_db, tax_data_setup):
        """Test tax calculation for income below threshold."""
        tax_year = tax_data_setup["tax_year"]
        
        # Add low income (below threshold of R95,750)
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Part-time",
            annual_amount=80000,
            tax_year=tax_year
        )
        test_db.add(income)
        test_db.commit()
        
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        
        assert result["gross_income"] == 80000
        assert result["taxable_income"] == 80000
        assert result["final_tax"] == 0  # Below threshold

    def test_calculate_tax_liability_with_income_and_expenses(self, calculator, test_user, test_db, tax_data_setup, expense_types_setup):
        """Test complete tax calculation with income and expenses."""
        tax_year = tax_data_setup["tax_year"]
        
        # Add income
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Salary",
            annual_amount=400000,
            tax_year=tax_year
        )
        test_db.add(income)
        
        # Add expense
        expense = UserExpense(
            user_id=test_user.id,
            expense_type_id=1,
            description="Retirement contribution",
            amount=50000,
            tax_year=tax_year
        )
        test_db.add(expense)
        test_db.commit()
        
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        
        assert result["gross_income"] == 400000
        assert result["taxable_income"] == 350000  # 400k - 50k expenses
        assert result["final_tax"] > 0
        assert result["effective_tax_rate"] > 0
        assert result["monthly_tax_rate"] > 0

    def test_calculate_tax_liability_user_not_found(self, calculator):
        """Test tax calculation for non-existent user."""
        with pytest.raises(ValueError, match="User with ID 99999 not found"):
            calculator.calculate_tax_liability(99999)

    def test_calculate_provisional_tax(self, calculator, test_user, test_db, tax_data_setup):
        """Test provisional tax calculation."""
        tax_year = tax_data_setup["tax_year"]
        
        # Add income for provisional taxpayer
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Consulting",
            annual_amount=500000,
            tax_year=tax_year
        )
        test_db.add(income)
        test_db.commit()
        
        result = calculator.calculate_provisional_tax(test_user.id, tax_year)
        
        assert "total_tax" in result
        assert "first_payment" in result
        assert "second_payment" in result
        assert result["total_tax"] > 0
        
        # Check payment structure
        first_payment = result["first_payment"]
        second_payment = result["second_payment"]
        
        assert "amount" in first_payment
        assert "due_date" in first_payment
        assert "amount" in second_payment
        assert "due_date" in second_payment
        
        # Payments should be equal (50% each)
        assert abs(first_payment["amount"] - second_payment["amount"]) < 1
        
        # Total payments should equal total tax
        total_payments = first_payment["amount"] + second_payment["amount"]
        assert abs(total_payments - result["total_tax"]) < 1

    def test_calculate_provisional_tax_non_provisional_user(self, calculator, test_admin_user, test_db, tax_data_setup):
        """Test provisional tax calculation for non-provisional taxpayer."""
        with pytest.raises(ValueError, match="not a provisional taxpayer"):
            calculator.calculate_provisional_tax(test_admin_user.id)

    def test_calculate_provisional_tax_due_dates(self, calculator, test_user, test_db, tax_data_setup):
        """Test that provisional tax due dates are correctly calculated."""
        tax_year = tax_data_setup["tax_year"]
        
        # Add income
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Freelance",
            annual_amount=300000,
            tax_year=tax_year
        )
        test_db.add(income)
        test_db.commit()
        
        result = calculator.calculate_provisional_tax(test_user.id, tax_year)
        
        # Check due date format and logic
        first_due = result["first_payment"]["due_date"]
        second_due = result["second_payment"]["due_date"]
        
        # Should be in YYYY-MM-DD format
        assert len(first_due) == 10
        assert len(second_due) == 10
        
        # First payment due on 31 August
        assert first_due.endswith("-08-31")
        
        # Second payment due on 28/29 February
        assert second_due.endswith("-02-28") or second_due.endswith("-02-29")