# app/utils/tax_utils.py
from datetime import date, datetime


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
