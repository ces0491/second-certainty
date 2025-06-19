# tests/test_core/test_tax_calculator
import pytest
from decimal import Decimal
from app.core.tax_calculator import TaxCalculator

class TestTaxCalculator:
    
    def test_calculate_income_tax_first_bracket(self):
        """Fixed test with proper precision handling"""
        calculator = TaxCalculator()
        
        # Test income in first bracket (18%)
        income = 200000.0
        expected = 36000.0  # 200000 * 0.18
        
        tax = calculator.calculate_income_tax(income)
        
        # Use appropriate tolerance for financial calculations
        assert abs(tax - expected) < 1.0  # Allow R1 difference
        
        # Alternative using pytest.approx
        # assert tax == pytest.approx(expected, abs=1.0)
    
    def test_calculate_income_tax_high_bracket(self):
        """Test the failing R350,000 income case"""
        calculator = TaxCalculator()
        
        # This was failing before - income of R350,000
        income = 350000.0
        
        # Should be in second bracket: R42,678 + 26% of amount over R237,100
        # (350000 - 237100) * 0.26 + 42678 = 112900 * 0.26 + 42678 = 29354 + 42678 = 72032
        expected = 72032.0
        
        tax = calculator.calculate_income_tax(income)
        
        assert abs(tax - expected) < 1.0
