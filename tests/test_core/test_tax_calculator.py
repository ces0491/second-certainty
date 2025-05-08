# tests/test_core/test_tax_calculator.py
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from app.core.tax_calculator import TaxCalculator
from app.models.tax_models import UserProfile, IncomeSource, UserExpense, TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit

class TestTaxCalculator:
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        
        # Set up mock tax brackets for 2024-2025
        brackets = [
            MagicMock(lower_limit=0, upper_limit=226000, rate=0.18, base_amount=0, tax_year="2024-2025"),
            MagicMock(lower_limit=226001, upper_limit=353100, rate=0.26, base_amount=40680, tax_year="2024-2025"),
            MagicMock(lower_limit=353101, upper_limit=488700, rate=0.31, base_amount=73726, tax_year="2024-2025"),
            MagicMock(lower_limit=488701, upper_limit=641400, rate=0.36, base_amount=115762, tax_year="2024-2025"),
            MagicMock(lower_limit=641401, upper_limit=817600, rate=0.39, base_amount=170734, tax_year="2024-2025"),
            MagicMock(lower_limit=817601, upper_limit=1731600, rate=0.41, base_amount=239452, tax_year="2024-2025"),
            MagicMock(lower_limit=1731601, upper_limit=None, rate=0.45, base_amount=614192, tax_year="2024-2025")
        ]
        
        # Set up mock rebates
        rebate = MagicMock(
            primary=17235, 
            secondary=9444, 
            tertiary=3145, 
            tax_year="2024-2025"
        )
        
        # Set up mock thresholds
        threshold = MagicMock(
            below_65=95750, 
            age_65_to_74=148217, 
            age_75_plus=165689, 
            tax_year="2024-2025"
        )
        
        # Set up mock medical credits
        medical_credit = MagicMock(
            main_member=347, 
            additional_member=347, 
            tax_year="2024-2025"
        )
        
        # Configure the query mock to return appropriate data
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = brackets
        db.query.return_value.filter.return_value.first.side_effect = [
            rebate,   # First call returns rebate
            threshold,  # Second call returns threshold
            medical_credit  # Third call returns medical credit
        ]
        
        return db
    
    @pytest.fixture
    def tax_calculator(self, mock_db):
        """Create a TaxCalculator instance with a mock database."""
        return TaxCalculator(mock_db)
    
    def test_get_tax_brackets(self, tax_calculator):
        """Test retrieving tax brackets."""
        brackets = tax_calculator.get_tax_brackets("2024-2025")
        
        assert len(brackets) == 7
        assert brackets[0]["lower_limit"] == 0
        assert brackets[0]["rate"] == 0.18
        assert brackets[-1]["lower_limit"] == 1731601
        assert brackets[-1]["upper_limit"] == None
    
    def test_calculate_income_tax_first_bracket(self, tax_calculator):
        """Test tax calculation for income in the first bracket."""
        tax = tax_calculator.calculate_income_tax(200000, "2024-2025")
        assert tax == 200000 * 0.18  # 18% of 200000
    
    def test_calculate_income_tax_middle_bracket(self, tax_calculator):
        """Test tax calculation for income in a middle bracket."""
        # Income in the third bracket (R353,101 - R488,700)
        income = 400000
        expected_tax = 73726 + 0.31 * (income - 353101)  # Base amount + 31% of amount over bracket lower limit
        tax = tax_calculator.calculate_income_tax(income, "2024-2025")
        assert round(tax, 2) == round(expected_tax, 2)
    
    def test_calculate_rebate(self, tax_calculator):
        """Test rebate calculation based on age."""
        # Under 65
        rebate_under_65 = tax_calculator.calculate_rebate(35, "2024-2025")
        assert rebate_under_65 == 17235  # Primary rebate only
        
        # Age 65
        rebate_65 = tax_calculator.calculate_rebate(65, "2024-2025")
        assert rebate_65 == 17235 + 9444  # Primary + secondary rebate
        
        # Age 75
        rebate_75 = tax_calculator.calculate_rebate(75, "2024-2025")
        assert rebate_75 == 17235 + 9444 + 3145  # Primary + secondary + tertiary rebate

    @patch('app.core.tax_calculator.calculate_age')
    def test_calculate_tax_liability(self, mock_calculate_age, tax_calculator, mock_db):
        """Test the complete tax liability calculation."""
        # Mock the user, income, and expenses
        mock_user = MagicMock(
            id=1,
            date_of_birth=date(1985, 1, 1)
        )
        
        mock_income_sources = [
            MagicMock(annual_amount=350000),
            MagicMock(annual_amount=50000)
        ]
        
        # Configure the mocks
        mock_calculate_age.return_value = 40
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,  # First call for user
            None,       # No result for another query
            None        # No result for another query
        ]
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            mock_income_sources,  # For income sources
            []                    # For expenses (none)
        ]
        
        # Mock the expense calculation
        tax_calculator.calculate_deductible_expenses = MagicMock(return_value=0)
        
        # Call the method
        result = tax_calculator.calculate_tax_liability(1, "2024-2025")
        
        # Verify results
        assert result["gross_income"] == 400000
        assert result["taxable_income"] == 400000
        
        # Calculate expected tax
        expected_tax_before_rebates = 73726 + 0.31 * (400000 - 353101)
        expected_final_tax = max(0, expected_tax_before_rebates - 17235 - 347)  # Tax - rebates - medical credit
        
        assert round(result["tax_before_rebates"], 2) == round(expected_tax_before_rebates, 2)
        assert round(result["final_tax"], 2) == round(expected_final_tax, 2)