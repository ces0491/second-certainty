# tests/test_api/test_tax_calculator.py
import pytest
from fastapi import status

def test_get_tax_brackets(authorized_client):
    """Test retrieving tax brackets."""
    response = authorized_client.get("/api/tax/tax-brackets/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "lower_limit" in data[0]
        assert "rate" in data[0]

def test_get_deductible_expense_types(authorized_client):
    """Test retrieving deductible expense types."""
    response = authorized_client.get("/api/tax/deductible-expenses/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

def test_add_income_unauthorized(client, test_user):
    """Test adding income without authorization."""
    income_data = {
        "source_type": "Salary",
        "description": "Monthly salary",
        "annual_amount": 350000,
        "is_paye": True
    }
    response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_add_income_authorized(authorized_client, test_user, test_db):
    """Test adding income with authorization."""
    income_data = {
        "source_type": "Salary",
        "description": "Monthly salary",
        "annual_amount": 350000,
        "is_paye": True
    }
    response = authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["source_type"] == income_data["source_type"]
    assert data["annual_amount"] == income_data["annual_amount"]
    assert data["user_id"] == test_user.id

def test_calculate_tax(authorized_client, test_user, test_db):
    """Test tax calculation endpoint."""
    # First add some income
    income_data = {
        "source_type": "Salary",
        "description": "Monthly salary",
        "annual_amount": 350000,
        "is_paye": True
    }
    authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
    
    # Then calculate tax
    response = authorized_client.get(f"/api/tax/users/{test_user.id}/tax-calculation/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Basic validation of the response structure
    assert "gross_income" in data
    assert "taxable_income" in data
    assert "final_tax" in data
    assert data["gross_income"] == 350000

def test_calculate_provisional_tax(authorized_client, test_user, test_db):
    """Test provisional tax calculation."""
    # First add some income
    income_data = {
        "source_type": "Salary",
        "description": "Monthly salary",
        "annual_amount": 350000,
        "is_paye": True
    }
    authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
    
    # Then calculate provisional tax
    response = authorized_client.get(f"/api/tax/users/{test_user.id}/provisional-tax/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Basic validation of the response structure
    assert "annual_tax" in data
    assert "first_payment" in data
    assert "second_payment" in data