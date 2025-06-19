#tests/test_core/test_tax_calculator
import pytest
from datetime import date
from unittest.mock import MagicMock

from app.core.tax_calculator import TaxCalculator
from app.models.tax_models import UserProfile, IncomeSource, UserExpense, TaxBracket, TaxRebate, TaxThreshold, MedicalTaxCredit

class TestTaxCalculator:

    @pytest.fixture
    def tax_calculator_with_real_data(self, test_db):
        """Create a TaxCalculator with real test data."""
        from app.utils.tax_utils import get_tax_year

        tax_year = get_tax_year()

        #Add real tax brackets
        brackets = [
            TaxBracket(lower_limit=1, upper_limit=237100, rate=0.18, base_amount=0, tax_year=tax_year),
            TaxBracket(lower_limit=237101, upper_limit=370500, rate=0.26, base_amount=42678, tax_year=tax_year),
            TaxBracket(lower_limit=370501, upper_limit=512800, rate=0.31, base_amount=77362, tax_year=tax_year),
            TaxBracket(lower_limit=512801, upper_limit=None, rate=0.36, base_amount=121475, tax_year=tax_year),
        ]

        for bracket in brackets:
            test_db.add(bracket)

        #Add rebates
        rebate = TaxRebate(
            primary=17235,
            secondary=9444,
            tertiary=3145,
            tax_year=tax_year
        )
        test_db.add(rebate)

        #Add thresholds
        threshold = TaxThreshold(
            below_65=95750,
            age_65_to_74=148217,
            age_75_plus=165689,
            tax_year=tax_year
        )
        test_db.add(threshold)

        #Add medical credits
        medical_credit = MedicalTaxCredit(
            main_member=347,
            additional_member=347,
            tax_year=tax_year
        )
        test_db.add(medical_credit)

        test_db.commit()

        return TaxCalculator(test_db)

    def test_get_tax_brackets(self, tax_calculator_with_real_data):
        """Test retrieving tax brackets with real data."""
        from app.utils.tax_utils import get_tax_year

        brackets = tax_calculator_with_real_data.get_tax_brackets(get_tax_year())

        assert len(brackets) == 4
        assert brackets[0]["lower_limit"] == 1
        assert brackets[0]["rate"] == 0.18
        assert brackets[-1]["upper_limit"] is None  #Highest bracket

    def test_calculate_income_tax_first_bracket(self, tax_calculator_with_real_data):
        """Test tax calculation for income in the first bracket."""
        from app.utils.tax_utils import get_tax_year

        tax = tax_calculator_with_real_data.calculate_income_tax(200000, get_tax_year())
        expected = 200000 * 0.18  #18% of 200000
        assert abs(tax - expected) < 0.01  #Allow for floating point precision

    def test_calculate_income_tax_second_bracket(self, tax_calculator_with_real_data):
        """Test tax calculation for income in the second bracket."""
        from app.utils.tax_utils import get_tax_year

        #Income in the second bracket (R237,101 - R370,500)
        income = 300000
        expected_tax = 42678 + 0.26 * (income - 237101)  #Base amount + 26% of amount over bracket lower limit
        tax = tax_calculator_with_real_data.calculate_income_tax(income, get_tax_year())
        assert abs(tax - expected_tax) < 0.01  #Allow for floating point precision

    def test_calculate_rebate(self, tax_calculator_with_real_data):
        """Test rebate calculation based on age."""
        from app.utils.tax_utils import get_tax_year

        #Under 65
        rebate_under_65 = tax_calculator_with_real_data.calculate_rebate(35, get_tax_year())
        assert rebate_under_65 == 17235  #Primary rebate only

        #Age 65
        rebate_65 = tax_calculator_with_real_data.calculate_rebate(65, get_tax_year())
        assert rebate_65 == 17235 + 9444  #Primary + secondary rebate

        #Age 75
        rebate_75 = tax_calculator_with_real_data.calculate_rebate(75, get_tax_year())
        assert rebate_75 == 17235 + 9444 + 3145  #Primary + secondary + tertiary rebate

    def test_calculate_tax_liability_with_real_user(self, tax_calculator_with_real_data, test_db):
        """Test the complete tax liability calculation with real user data."""
        from app.utils.tax_utils import get_tax_year

        #Create a real user
        user = UserProfile(
            email="test_calc@example.com",
            hashed_password="hashed",
            name="Test",
            surname="Calculator",
            date_of_birth=date(1985, 1, 1),
            is_provisional_taxpayer=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        #Add income source
        income = IncomeSource(
            user_id=user.id,
            source_type="Salary",
            description="Test salary",
            annual_amount=350000,
            is_paye=True,
            tax_year=get_tax_year()
        )
        test_db.add(income)
        test_db.commit()

        #Calculate tax liability
        result = tax_calculator_with_real_data.calculate_tax_liability(user.id, get_tax_year())

        #Verify results
        assert result["gross_income"] == 350000
        assert result["taxable_income"] == 350000  #No deductions
        assert result["final_tax"] >= 0  #Should have some tax
        assert result["effective_tax_rate"] >= 0

    def test_calculate_medical_credit(self, tax_calculator_with_real_data):
        """Test medical credit calculation."""
        from app.utils.tax_utils import get_tax_year

        #Test with 1 main member, 0 additional
        credit = tax_calculator_with_real_data.calculate_medical_credit(1, 0, get_tax_year())
        assert credit == 347

        #Test with 1 main member, 2 additional
        credit = tax_calculator_with_real_data.calculate_medical_credit(1, 2, get_tax_year())
        assert credit == 347 + (2 * 347)  #347 * 3

    def test_calculate_tax_threshold(self, tax_calculator_with_real_data):
        """Test tax threshold calculation based on age."""
        from app.utils.tax_utils import get_tax_year

        #Under 65
        threshold = tax_calculator_with_real_data.calculate_tax_threshold(35, get_tax_year())
        assert threshold == 95750

        #Age 65-74
        threshold = tax_calculator_with_real_data.calculate_tax_threshold(70, get_tax_year())
        assert threshold == 148217

        #Age 75+
        threshold = tax_calculator_with_real_data.calculate_tax_threshold(80, get_tax_year())
        assert threshold == 165689
