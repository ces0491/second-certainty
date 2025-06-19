# app/utils/tax_utils.py
from datetime import date, datetime
from typing import Tuple


def get_tax_year() -> str:
    """
    Determine the current tax year in South Africa.
    Tax years run from March 1 to February 28/29 of the following year.

    Returns a string in the format "2024-2025"
    """
    now = datetime.now()
    current_year = now.year

    # South African tax year starts on March 1
    # If current date is before March 1, we're still in the previous tax year
    if now.month < 3:
        tax_year_start = current_year - 1
        tax_year_end = current_year
    else:
        tax_year_start = current_year
        tax_year_end = current_year + 1

    return f"{tax_year_start}-{tax_year_end}"


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
    Validate South African ID number with corrected Luhn algorithm.

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
    try:
        birth_month = int(id_number[2:4])
        birth_day = int(id_number[4:6])
    except ValueError:
        return False, "Invalid date components in ID number"

    # Basic date validation
    if birth_month < 1 or birth_month > 12:
        return False, "Invalid month in ID number"

    if birth_day < 1 or birth_day > 31:
        return False, "Invalid day in ID number"

    # Citizenship indicator validation
    citizenship = int(id_number[10])
    if citizenship not in [0, 1]:
        return False, "Invalid citizenship indicator"

    # Luhn algorithm check digit validation
    check_digit = int(id_number[12])

    # Calculate checksum using Luhn algorithm for SA ID numbers
    # Take first 12 digits
    id_digits = [int(d) for d in id_number[:12]]

    # Sum odd-positioned digits (1st, 3rd, 5th, etc.) - 0-indexed positions 0, 2, 4, ...
    odd_sum = sum(id_digits[i] for i in range(0, 12, 2))

    # For even-positioned digits (2nd, 4th, 6th, etc.) - 0-indexed positions 1, 3, 5, ...
    # Concatenate them into a single number, multiply by 2, then sum individual digits
    even_digits_str = "".join(str(id_digits[i]) for i in range(1, 12, 2))
    even_doubled = int(even_digits_str) * 2
    even_sum = sum(int(digit) for digit in str(even_doubled))

    # Calculate total and check digit
    total = odd_sum + even_sum
    calculated_check = (10 - (total % 10)) % 10

    if calculated_check != check_digit:
        return False, "Invalid check digit"

    return True, "Valid ID number"


def extract_birth_date_from_id(id_number: str) -> date:
    """Extract birth date from South African ID number."""
    is_valid, error = validate_id_number(id_number)
    if not is_valid:
        raise ValueError(error)

    # Determine century based on current year logic
    year_suffix = int(id_number[0:2])    # current_century_start = current_year - (current_year % 100)

    # If year suffix > 20, assume 1900s, otherwise 2000s
    # This is a simplified heuristic and may need adjustment over time
    if year_suffix > 20:
        birth_year = 1900 + year_suffix
    else:
        birth_year = 2000 + year_suffix

    birth_month = int(id_number[2:4])
    birth_day = int(id_number[4:6])

    try:
        return date(birth_year, birth_month, birth_day)
    except ValueError as e:
        raise ValueError(f"Invalid date components in ID number: {e}")


def get_gender_from_id(id_number: str) -> str:
    """Extract gender from South African ID number."""
    is_valid, error = validate_id_number(id_number)
    if not is_valid:
        raise ValueError(error)

    gender_digit = int(id_number[6])
    return "Male" if gender_digit >= 5 else "Female"


def is_sa_citizen_from_id(id_number: str) -> bool:
    """Check if person is SA citizen based on ID number."""
    is_valid, error = validate_id_number(id_number)
    if not is_valid:
        raise ValueError(error)

    citizenship_digit = int(id_number[10])
    return citizenship_digit == 0  # 0 = SA citizen, 1 = permanent resident
