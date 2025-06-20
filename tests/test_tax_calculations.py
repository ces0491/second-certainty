# tests/test_tax_calculations.py
import pytest
from app.core.tax_calculator import TaxCalculator
from app.models.tax_models import IncomeSource, UserExpense

class TestTaxCalculations:
    """Test tax calculation functionality."""
    
    def test_simple_tax_calculation(self, test_db, test_user, complete_tax_data):
        """Test basic tax calculation with single income source."""
        tax_year = complete_tax_data
        
        # Add income
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Salary",
            annual_amount=300000,
            tax_year=tax_year
        )
        test_db.add(income)
        test_db.commit()
        
        calculator = TaxCalculator(test_db)
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        
        assert result["gross_income"] == 300000
        assert result["taxable_income"] == 300000
        assert result["final_tax"] > 0
        assert result["effective_tax_rate"] > 0
    
    def test_tax_calculation_below_threshold(self, test_db, test_user, complete_tax_data):
        """Test tax calculation for income below threshold."""
        tax_year = complete_tax_data
        
        # Add low income
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Part-time",
            annual_amount=80000,  # Below R95,750 threshold
            tax_year=tax_year
        )
        test_db.add(income)
        test_db.commit()
        
        calculator = TaxCalculator(test_db)
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        
        assert result["gross_income"] == 80000
        assert result["final_tax"] == 0  # Below threshold
    
    def test_tax_calculation_with_deductions(self, test_db, test_user, complete_tax_data):
        """Test tax calculation with deductible expenses."""
        tax_year = complete_tax_data
        
        # Add income
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Salary",
            annual_amount=400000,
            tax_year=tax_year
        )
        test_db.add(income)
        
        # Add deduction
        expense = UserExpense(
            user_id=test_user.id,
            expense_type_id=1,  # Retirement Annuity
            description="Monthly RA contribution",
            amount=60000,
            tax_year=tax_year
        )
        test_db.add(expense)
        test_db.commit()
        
        calculator = TaxCalculator(test_db)
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        
        assert result["gross_income"] == 400000
        assert result["taxable_income"] == 340000  # 400k - 60k
        assert result["final_tax"] > 0
    
    def test_high_income_tax_calculation(self, test_db, test_user, complete_tax_data):
        """Test tax calculation for high income (45% bracket)."""
        tax_year = complete_tax_data
        
        # Add high income
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Executive Salary",
            annual_amount=2000000,  # Above R1,817,000
            tax_year=tax_year
        )
        test_db.add(income)
        test_db.commit()
        
        calculator = TaxCalculator(test_db)
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        
        assert result["gross_income"] == 2000000
        assert result["final_tax"] > 600000  # Should be substantial
        assert result["effective_tax_rate"] > 0.30  # Should be high
    
    def test_provisional_tax_calculation(self, test_db, test_user, complete_tax_data):
        """Test provisional tax calculations."""
        tax_year = complete_tax_data
        
        # Add consulting income
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Consulting",
            annual_amount=500000,
            is_paye=False,
            tax_year=tax_year
        )
        test_db.add(income)
        test_db.commit()
        
        calculator = TaxCalculator(test_db)
        result = calculator.calculate_provisional_tax(test_user.id, tax_year)
        
        assert "total_tax" in result
        assert "first_payment" in result
        assert "second_payment" in result
        
        # Payments should be equal (50% each)
        first_amount = result["first_payment"]["amount"]
        second_amount = result["second_payment"]["amount"]
        assert abs(first_amount - second_amount) < 1
        
        # Total should equal sum of payments
        total_payments = first_amount + second_amount
        assert abs(total_payments - result["total_tax"]) < 1
    
    def test_provisional_tax_due_dates(self, test_db, test_user, complete_tax_data):
        """Test provisional tax due dates are correct."""
        tax_year = complete_tax_data
        year_start = int(tax_year.split("-")[0])
        year_end = int(tax_year.split("-")[1])
        
        # Add income
        income = IncomeSource(
            user_id=test_user.id,
            source_type="Freelance",
            annual_amount=300000,
            tax_year=tax_year
        )
        test_db.add(income)
        test_db.commit()
        
        calculator = TaxCalculator(test_db)
        result = calculator.calculate_provisional_tax(test_user.id, tax_year)
        
        # Check due dates
        first_due = result["first_payment"]["due_date"]
        second_due = result["second_payment"]["due_date"]
        
        assert first_due == f"{year_start}-08-31"  # 31 August
        assert second_due.startswith(f"{year_end}-02-2")  # 28/29 February
    
    def test_age_based_rebates(self, test_db, complete_tax_data):
        """Test that age affects rebates correctly."""
        calculator = TaxCalculator(test_db)
        tax_year = complete_tax_data
        
        # Young person (< 65)
        young_rebate = calculator.calculate_rebate(30, tax_year)
        assert young_rebate == 17235  # Primary only
        
        # Senior (65-74)
        senior_rebate = calculator.calculate_rebate(70, tax_year)
        assert senior_rebate == 17235 + 9444  # Primary + secondary
        
        # Elderly (75+)
        elderly_rebate = calculator.calculate_rebate(80, tax_year)
        assert elderly_rebate == 17235 + 9444 + 3145  # All three
    
    def test_medical_tax_credits(self, test_db, complete_tax_data):
        """Test medical tax credit calculations."""
        calculator = TaxCalculator(test_db)
        tax_year = complete_tax_data
        
        # Single person
        single_credit = calculator.calculate_medical_credit(1, 0, tax_year)
        assert single_credit == 347
        
        # Couple
        couple_credit = calculator.calculate_medical_credit(1, 1, tax_year)
        assert couple_credit == 694  # 347 * 2
        
        # Family with 2 dependents
        family_credit = calculator.calculate_medical_credit(1, 2, tax_year)
        assert family_credit == 1041  # 347 * 3
    
    def test_tax_brackets_calculation(self, test_db, complete_tax_data):
        """Test that tax is calculated correctly across different brackets."""
        calculator = TaxCalculator(test_db)
        tax_year = complete_tax_data
        
        # Test first bracket (18%)
        tax_200k = calculator.calculate_income_tax(200000, tax_year)
        expected_200k = 200000 * 0.18  # 36,000
        assert abs(tax_200k - expected_200k) < 1.0
        
        # Test second bracket (26%)
        tax_300k = calculator.calculate_income_tax(300000, tax_year)
        expected_300k = 42678 + (0.26 * (300000 - 237100))  # Base + rate on excess
        assert abs(tax_300k - expected_300k) < 1.0
        
        # Test highest bracket (45%)
        tax_2m = calculator.calculate_income_tax(2000000, tax_year)
        expected_2m = 644489 + (0.45 * (2000000 - 1817000))
        assert abs(tax_2m - expected_2m) < 1.0
    
    def test_no_income_scenario(self, test_db, test_user, complete_tax_data):
        """Test tax calculation with no income."""
        tax_year = complete_tax_data
        
        calculator = TaxCalculator(test_db)
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        
        assert result["gross_income"] == 0
        assert result["taxable_income"] == 0
        assert result["final_tax"] == 0
        assert result["effective_tax_rate"] == 0
    
    def test_multiple_income_sources(self, test_db, test_user, complete_tax_data):
        """Test tax calculation with multiple income sources."""
        tax_year = complete_tax_data
        
        # Add multiple income sources
        incomes = [
            {"source_type": "Salary", "amount": 250000},
            {"source_type": "Freelance", "amount": 100000},
            {"source_type": "Investment", "amount": 50000},
        ]
        
        for income_data in incomes:
            income = IncomeSource(
                user_id=test_user.id,
                source_type=income_data["source_type"],
                annual_amount=income_data["amount"],
                tax_year=tax_year
            )
            test_db.add(income)
        test_db.commit()
        
        calculator = TaxCalculator(test_db)
        result = calculator.calculate_tax_liability(test_user.id, tax_year)
        
        assert result["gross_income"] == 400000  # Sum of all incomes
        assert result["final_tax"] > 0
    
    def test_provisional_tax_non_provisional_user(self, test_db, admin_user, complete_tax_data):
        """Test that non-provisional taxpayers can't calculate provisional tax."""
        tax_year = complete_tax_data
        
        calculator = TaxCalculator(test_db)
        
        with pytest.raises(ValueError, match="not a provisional taxpayer"):
            calculator.calculate_provisional_tax(admin_user.id, tax_year)