# tests/test_data_validation.py
from datetime import date
from unittest.mock import patch

import pytest

from app.utils.tax_utils import (
    calculate_age,
    format_currency,
)


class TestDataValidation:
    """Test data validation functions (ID validation removed as not used in app)."""

    def test_format_currency(self):
        """Test currency formatting utility."""
        assert format_currency(1000) == "R 1,000.00"
        assert format_currency(1234567.89) == "R 1,234,567.89"
        assert format_currency(0) == "R 0.00"
        assert format_currency(-500) == "R -500.00"
        assert format_currency(100.5) == "R 100.50"

    def test_age_calculation_validation(self):
        """Test age calculation with various dates."""
        birth_date = date(1990, 6, 15)

        # Test birthday not yet reached this year
        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 3, 1)
            age = calculate_age(birth_date)
            assert age == 34

        # Test birthday already passed this year
        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 8, 1)
            age = calculate_age(birth_date)
            assert age == 35

        # Test exact birthday
        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            age = calculate_age(birth_date)
            assert age == 35

    def test_input_sanitization(self):
        """Test that inputs are properly sanitized."""
        # Test currency formatting with various inputs
        assert format_currency(1000.0) == "R 1,000.00"
        assert format_currency(1000) == "R 1,000.00"

    def test_date_boundary_validation(self):
        """Test date boundary validation."""
        # Test leap year dates
        leap_year_birth = date(2000, 2, 29)
        
        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 3, 1)
            age = calculate_age(leap_year_birth)
            assert age == 25

    def test_age_calculation_edge_cases(self):
        """Test edge cases in age calculation."""
        # Test with very recent birth date
        recent_birth = date(2024, 12, 31)
        
        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 1, 1)
            age = calculate_age(recent_birth)
            assert age == 0

        # Test with very old birth date
        old_birth = date(1900, 1, 1)
        
        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            age = calculate_age(old_birth)
            assert age == 125

    def test_currency_formatting_edge_cases(self):
        """Test currency formatting with edge cases."""
        # Test very large numbers
        assert format_currency(999999999.99) == "R 999,999,999.99"
        
        # Test very small positive numbers
        assert format_currency(0.01) == "R 0.01"
        
        # Test negative numbers
        assert format_currency(-1234.56) == "R -1,234.56"
        
        # Test zero variants
        assert format_currency(0.0) == "R 0.00"
        assert format_currency(-0.0) == "R 0.00"

    def test_age_calculation_performance(self):
        """Test that age calculation is performant."""
        import time
        
        birth_date = date(1990, 6, 15)
        
        start_time = time.time()
        for _ in range(1000):
            age = calculate_age(birth_date)
        end_time = time.time()
        
        # Should complete 1000 calculations in less than 0.1 seconds
        assert (end_time - start_time) < 0.1
        assert age >= 0  # Sanity check

    def test_data_validation_consistency(self):
        """Test that validation functions return consistent results."""
        # Test that multiple calls to the same function return the same result
        birth_date = date(1985, 3, 15)
        
        with patch("app.utils.tax_utils.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            
            ages = [calculate_age(birth_date) for _ in range(10)]
            assert all(age == ages[0] for age in ages)
            assert ages[0] == 40

    def test_currency_formatting_consistency(self):
        """Test currency formatting consistency."""
        amount = 1234.56
        
        # Multiple calls should return the same result
        formatted_amounts = [format_currency(amount) for _ in range(10)]
        assert all(formatted == formatted_amounts[0] for formatted in formatted_amounts)
        assert formatted_amounts[0] == "R 1,234.56"

    def test_invalid_date_handling(self):
        """Test handling of edge case dates."""
        # Test with today's date as birth date (age 0)
        with patch("app.utils.tax_utils.date") as mock_date:
            today = date(2025, 6, 15)
            mock_date.today.return_value = today
            
            age = calculate_age(today)
            assert age == 0

    def test_leap_year_birthday_edge_cases(self):
        """Test leap year birthday calculations."""
        # Born on leap day
        leap_birth = date(2000, 2, 29)
        
        # Test in non-leap year
        with patch("app.utils.tax_utils.date") as mock_date:
            # Before leap day equivalent in non-leap year
            mock_date.today.return_value = date(2025, 2, 28)
            age = calculate_age(leap_birth)
            assert age == 24  # Birthday hasn't happened yet
            
            # After leap day equivalent in non-leap year
            mock_date.today.return_value = date(2025, 3, 1)
            age = calculate_age(leap_birth)
            assert age == 25  # Birthday has happened

    def test_currency_precision(self):
        """Test currency formatting precision."""
        # Test various decimal places
        test_cases = [
            (1234.1, "R 1,234.10"),
            (1234.12, "R 1,234.12"),
            (1234.123, "R 1,234.12"),  # Should round to 2 decimal places
            (1234.126, "R 1,234.13"),  # Should round up
            (1234.125, "R 1,234.12"),  # Banker's rounding (round to even)
        ]
        
        for amount, expected in test_cases:
            result = format_currency(amount)
            assert result == expected, f"Expected {expected}, got {result} for amount {amount}"