# tests/test_utils/test_tax_utils
import pytest
from unittest.mock import patch, call, MagicMock
from app.utils.tax_utils import get_citizenship_indicator, validate_id_number

def test_citizenship_indicator():
    """Fixed test with proper mock path and setup"""
    
    # Mock the validate_id_number function properly
    with patch('app.utils.tax_utils.validate_id_number') as mock_validate:
        # Set up mock to return True for valid calls
        mock_validate.return_value = True
        
        # Test South African citizen (citizenship digit = 0)
        result1 = get_citizenship_indicator("9001010001080")  # SA citizen
        assert result1 == "South African"
        
        # Test foreign national (citizenship digit = 1) 
        result2 = get_citizenship_indicator("9001010001181")  # Foreign national
        assert result2 == "Foreign National"
        
        # Verify the mock was called exactly twice
        assert mock_validate.call_count == 2
        
        # Verify the calls were made with expected arguments
        expected_calls = [
            call("9001010001080"),
            call("9001010001181")
        ]
        mock_validate.assert_has_calls(expected_calls)

def test_citizenship_indicator_invalid_id():
    """Test citizenship indicator with invalid ID"""
    
    with patch('app.utils.tax_utils.validate_id_number') as mock_validate:
        # Set up mock to return False for invalid ID
        mock_validate.return_value = False
        
        result = get_citizenship_indicator("invalid_id")
        assert result == "Invalid"
        
        mock_validate.assert_called_once_with("invalid_id")
