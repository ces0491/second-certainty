# app/utils/tax_utils.py
from datetime import datetime, date
from typing import Tuple

def get_tax_year() -> str:
    """
    Determine the current tax year in South Africa.
    Tax years run from March 1 to February 28/29 of the following year.
    
    Returns a string in the format "2024-2025"
    """
    today = datetime.now()
    current_year = today.year
    
    # If we're in January or February, we're in the tax year that started in the previous calendar year
    if today.month < 3:
        return f"{current_year-1}-{current_year}"
    else:
        return f"{current_year}-{current_year+1}"

def calculate_age(birth_date: date) -> int:
    """Calculate age based on birth date."""
    today = date.today()
    age = today.year - birth_date.year
    
    # Check if birthday has occurred this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age

def format_currency(amount: float) -> str:
    """Format amount as South African Rand."""
    return f"R {amount:,.2f}"

def validate_id_number(id_number: str) -> Tuple[bool, str]:
    """
    Validate South African ID number.
    
    Returns a tuple of (is_valid, error_message)
    """
    # Basic checks
    if not id_number or not isinstance(id_number, str):
        return False, "ID number must be a string"
    
    if len(id_number) != 13:
        return False, "ID number must be 13 digits"
    
    if not id_number.isdigit():
        return False, "ID number must contain only digits"
    
    # Extract components
    birth_year = int(id_number[0:2])
    birth_month = int(id_number[2:4])
    birth_day = int(id_number[4:6])
    
    # Basic date validation
    if birth_month < 1 or birth_month > 12:
        return False, "Invalid month in ID number"
    
    if birth_day < 1 or birth_day > 31:
        return False, "Invalid day in ID number"
    
    # Citizenship
    citizenship = int(id_number[10])
    if citizenship not in [0, 1]:
        return False, "Invalid citizenship indicator"
    
    # Luhn algorithm check digit
    check_digit = int(id_number[12])
    
    # Calculate checksum
    odds = sum(int(id_number[i]) for i in range(0, 12, 2))
    evens = ''.join(id_number[i] for i in range(1, 12, 2))
    evens_times_2 = str(int(evens) * 2)
    evens_sum = sum(int(digit) for digit in evens_times_2)
    
    total = odds + evens_sum
    check = (10 - (total % 10)) % 10
    
    if check != check_digit:
        return False, "Invalid check digit"
    
    return True, "Valid ID number"

def extract_birth_date_from_id(id_number: str) -> date:
    """Extract birth date from South African ID number."""
    is_valid, error = validate_id_number(id_number)
    if not is_valid:
        raise ValueError(error)
    
    year_prefix = "19" if int(id_number[0:2]) > 20 else "20"
    birth_year = int(f"{year_prefix}{id_number[0:2]}")
    birth_month = int(id_number[2:4])
    birth_day = int(id_number[4:6])
    
    return date(birth_year, birth_month, birth_day)