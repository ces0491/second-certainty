# tests/test_utils/test_tax_utils.py
import pytest
from datetime import date, datetime
from unittest.mock import patch
from app.utils.tax_utils import (
    get_tax_year, calculate_age, format_currency, 
    validate_id_number, extract_birth_date_from_id
)

def test_get_tax_year():
    """Test determining the current tax year."""
    # Test for a date in March (start of tax year)
    with patch('app.utils.tax_utils.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 3, 1)
        assert get_tax_year() == "2025-2026"
    
    # Test for a date in February (end of tax year)
    with patch('app.utils.tax_utils.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 2, 28)
        assert get_tax_year() == "2024-2025"

def test_calculate_age():
    """Test age calculation."""
    today = date(2025, 5, 1)
    
    with patch('app.utils.tax_utils.date') as mock_date:
        mock_date.today.return_value = today
        
        # Test when birthday has occurred this year
        birth_date = date(1990, 4, 15)
        assert calculate_age(birth_date) == 35
        
        # Test when birthday has not yet occurred this year
        birth_date = date(1990, 6, 15)
        assert calculate_age(birth_date) == 34
        
        # Test when birthday is today
        birth_date = date(1990, 5, 1)
        assert calculate_age(birth_date) == 35

def test_format_currency():
    """Test currency formatting."""
    assert format_currency(1000) == "R 1,000.00"
    assert format_currency(1234567.89) == "R 1,234,567.89"
    assert format_currency(0) == "R 0.00"

def test_validate_id_number():
    """Test South African ID number validation."""
    # Valid ID number (example)
    is_valid, message = validate_id_number("9001015009087")
    assert is_valid
    assert "Valid" in message
    
    # Too short
    is_valid, message = validate_id_number("90010150090")
    assert not is_valid
    assert "13 digits" in message
    
    # Non-digit characters
    is_valid, message = validate_id_number("90010150090AB")
    assert not is_valid
    assert "digits" in message
    
    # Invalid month
    is_valid, message = validate_id_number("9013015009087")
    assert not is_valid
    assert "month" in message
    
    # Invalid day
    is_valid, message = validate_id_number("9001325009087")
    assert not is_valid
    assert "day" in message

def test_extract_birth_date_from_id():
    """Test extracting birth date from ID number."""
    # Mock the validate_id_number function to always return valid
    with patch('app.utils.tax_utils.validate_id_number', return_value=(True, "Valid")):
        # ID for someone born on January 1, 1990
        birth_date = extract_birth_date_from_id("9001015009087")
        assert birth_date == date(1990, 1, 1)
        
        # ID for someone born on December 31, 2005
        birth_date = extract_birth_date_from_id("0512315009087")
        assert birth_date == date(2005, 12, 31)