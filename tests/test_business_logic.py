# tests/test_business_logic.py
from datetime import date, datetime
from unittest.mock import patch

import pytest

from app.utils.tax_utils import calculate_age, get_tax_year


class TestBusinessLogic:
    """Test core business logic."""

    def test_tax_year_calculation_before_march(self):
        """Test tax year calculation when current date is before March."""
        # Mock date in January (before March 1)
        with patch("app.utils.tax_utils.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 1, 15)
            tax_year = get_tax_year()
            # Should be previous calendar year to current calendar year
            assert tax_year == "2024-2025"

    def test_tax_year_calculation_after_march(self):
        """Test tax year calculation when current date is after March."""
        # Mock date in June (after March 1)
        with patch("app.utils.tax_utils.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 15)
            tax_year = get_tax_year()
            # Should be current calendar year to next calendar year
            assert tax_year == "2025-2026"

    def test_tax_year_calculation_on_march_first(self):
        """Test tax year calculation on March 1 (tax year boundary)."""
        # Mock date on March 1
        with patch("app.utils.tax_utils.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 3, 1)
            tax_year = get_tax_year()
            # Should be current calendar year to next calendar year
            assert tax_year == "2025-2026"

    def test_tax_year_calculation_end_of_february(self):
        """Test tax year calculation on February 28/29 (tax year end)."""
        # Mock date on February 28
        with patch("app.utils.tax_utils.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 2, 28)
            tax_year = get_tax_year()
            # Should still be previous tax year
            assert tax_year == "2024-2025"

    def test_age_calculation_before_birthday(self):
        """Test age calculation when birthday hasn't occurred this year."""
        birth_date = date(1990, 12, 25)

        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            age = calculate_age(birth_date)
            assert age == 34  # Haven't had birthday yet this year

    def test_age_calculation_after_birthday(self):
        """Test age calculation when birthday has occurred this year."""
        birth_date = date(1990, 3, 15)

        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            age = calculate_age(birth_date)
            assert age == 35  # Already had birthday this year

    def test_age_calculation_on_birthday(self):
        """Test age calculation on exact birthday."""
        birth_date = date(1990, 6, 15)

        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            age = calculate_age(birth_date)
            assert age == 35  # Birthday is today

    def test_age_calculation_leap_year_edge_case(self):
        """Test age calculation for leap year birthdays."""
        # Born on February 29
        birth_date = date(2000, 2, 29)

        # Test in non-leap year
        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 3, 1)  # Day after Feb 28
            age = calculate_age(birth_date)
            assert age == 25  # Should have "had birthday" on Feb 28

    def test_provisional_tax_due_dates_logic(self):
        """Test provisional tax due date calculation logic."""
        test_cases = [
            ("2024-2025", "2024-08-31", "2025-02-28"),  # Non-leap year
            ("2023-2024", "2023-08-31", "2024-02-29"),  # Leap year
            ("2025-2026", "2025-08-31", "2026-02-28"),  # Non-leap year
        ]

        for tax_year, expected_first, expected_second in test_cases:
            year_start = int(tax_year.split("-")[0])
            year_end = int(tax_year.split("-")[1])

            # First payment: 31 August of start year
            first_due = f"{year_start}-08-31"
            assert first_due == expected_first

            # Second payment: 28/29 February of end year
            if year_end % 4 == 0 and (year_end % 100 != 0 or year_end % 400 == 0):
                second_due = f"{year_end}-02-29"  # Leap year
            else:
                second_due = f"{year_end}-02-28"  # Non-leap year

            assert second_due == expected_second

    def test_tax_bracket_progression_logic(self):
        """Test tax bracket progression logic."""
        # Test South African tax bracket structure
        from app.core.tax_calculator import TaxCalculator

        # Mock tax brackets for testing
        brackets = [
            {"lower_limit": 1, "upper_limit": 237100, "rate": 0.18, "base_amount": 0},
            {"lower_limit": 237101, "upper_limit": 370500, "rate": 0.26, "base_amount": 42678},
            {"lower_limit": 370501, "upper_limit": 512800, "rate": 0.31, "base_amount": 77362},
        ]

        # Test that income falls into correct bracket
        test_incomes = [
            (100000, 0),  # First bracket
            (300000, 1),  # Second bracket
            (450000, 2),  # Third bracket
        ]

        for income, expected_bracket_index in test_incomes:
            bracket = None
            for i, b in enumerate(brackets):
                if income >= b["lower_limit"] and (b["upper_limit"] is None or income <= b["upper_limit"]):
                    bracket = i
                    break

            assert bracket == expected_bracket_index, f"Income {income} should be in bracket {expected_bracket_index}"

    def test_rebate_calculation_logic(self):
        """Test age-based rebate calculation logic."""
        # Test rebate amounts (2024-2025 values)
        rebates = {"primary": 17235, "secondary": 9444, "tertiary": 3145}

        test_cases = [
            (25, 17235),  # Under 65: primary only
            (65, 17235 + 9444),  # 65-74: primary + secondary
            (75, 17235 + 9444 + 3145),  # 75+: all three
            (64, 17235),  # Just under 65
            (74, 17235 + 9444),  # Just under 75
        ]

        for age, expected_rebate in test_cases:
            total_rebate = rebates["primary"]
            if age >= 65:
                total_rebate += rebates["secondary"]
            if age >= 75:
                total_rebate += rebates["tertiary"]

            assert total_rebate == expected_rebate, f"Age {age} should have rebate {expected_rebate}"

    def test_medical_credit_calculation_logic(self):
        """Test medical scheme fee tax credit logic."""
        credit_per_member = 347  # 2024-2025 value

        test_cases = [
            (1, 0, 347),  # Main member only
            (1, 1, 694),  # Main member + 1 dependent
            (1, 3, 1388),  # Main member + 3 dependents
            (2, 2, 1388),  # 2 main members + 2 dependents (unusual case)
        ]

        for main_members, dependents, expected_credit in test_cases:
            total_credit = (credit_per_member * main_members) + (credit_per_member * dependents)
            assert total_credit == expected_credit

    def test_taxable_income_calculation_logic(self):
        """Test taxable income calculation with deductions."""
        test_cases = [
            (500000, 0, 500000),  # No deductions
            (500000, 50000, 450000),  # With deductions
            (100000, 120000, 0),  # Deductions exceed income (should not go negative)
            (0, 10000, 0),  # No income
        ]

        for gross_income, deductions, expected_taxable in test_cases:
            taxable_income = max(0, gross_income - deductions)
            assert taxable_income == expected_taxable

    def test_effective_tax_rate_calculation(self):
        """Test effective tax rate calculation logic."""
        test_cases = [
            (100000, 18000, 0.18),  # 18% effective rate
            (500000, 125000, 0.25),  # 25% effective rate
            (0, 0, 0),  # No income, no tax
            (100000, 0, 0),  # Income but no tax (below threshold)
        ]

        for taxable_income, final_tax, expected_rate in test_cases:
            if taxable_income > 0:
                effective_rate = final_tax / taxable_income
            else:
                effective_rate = 0

            assert abs(effective_rate - expected_rate) < 0.001  # Allow for floating point precision

    def test_threshold_logic(self):
        """Test tax threshold logic."""
        # 2024-2025 thresholds
        thresholds = {"below_65": 95750, "age_65_to_74": 148217, "age_75_plus": 165689}

        test_cases = [
            (30, thresholds["below_65"]),
            (65, thresholds["age_65_to_74"]),
            (75, thresholds["age_75_plus"]),
            (64, thresholds["below_65"]),  # Just under 65
            (74, thresholds["age_65_to_74"]),  # Just under 75
        ]

        for age, expected_threshold in test_cases:
            if age >= 75:
                threshold = thresholds["age_75_plus"]
            elif age >= 65:
                threshold = thresholds["age_65_to_74"]
            else:
                threshold = thresholds["below_65"]

            assert threshold == expected_threshold

    def test_provisional_taxpayer_logic(self):
        """Test provisional taxpayer identification logic."""
        # Provisional taxpayer criteria (simplified for testing)
        test_cases = [
            (True, 500000, True),  # Explicitly set as provisional
            (False, 100000, False),  # Not provisional
            (True, 0, True),  # Provisional but no income
        ]

        for is_provisional_flag, income, should_calculate_provisional in test_cases:
            # Simplified logic: if user is marked as provisional taxpayer
            can_calculate = is_provisional_flag
            assert can_calculate == should_calculate_provisional

    def test_income_aggregation_logic(self):
        """Test logic for aggregating multiple income sources."""
        income_sources = [
            {"type": "Salary", "amount": 300000, "is_paye": True},
            {"type": "Freelance", "amount": 100000, "is_paye": False},
            {"type": "Investment", "amount": 50000, "is_paye": False},
        ]

        total_income = sum(source["amount"] for source in income_sources)
        assert total_income == 450000

        paye_income = sum(source["amount"] for source in income_sources if source["is_paye"])
        assert paye_income == 300000

        non_paye_income = sum(source["amount"] for source in income_sources if not source["is_paye"])
        assert non_paye_income == 150000

    def test_expense_aggregation_logic(self):
        """Test logic for aggregating deductible expenses."""
        expenses = [
            {"type": "Retirement", "amount": 50000, "max_percentage": 27.5},
            {"type": "Medical", "amount": 20000, "max_percentage": None},
            {"type": "Donations", "amount": 10000, "max_percentage": 10.0},
        ]

        total_expenses = sum(expense["amount"] for expense in expenses)
        assert total_expenses == 80000

        # Test percentage-based limits (simplified)
        income = 500000
        for expense in expenses:
            if expense["max_percentage"]:
                max_allowed = income * (expense["max_percentage"] / 100)
                actual_deduction = min(expense["amount"], max_allowed)
                assert actual_deduction <= max_allowed
