#tests/test_api/test_tax_calculator
import pytest
from fastapi import status


def test_get_tax_brackets(authorized_client):
    """Test retrieving tax brackets."""
    response = authorized_client.get("/api/tax/tax-brackets/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_get_deductible_expense_types(authorized_client):
    """Test retrieving deductible expense types."""
    response = authorized_client.get("/api/tax/deductible-expenses/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_add_income_unauthorized(client, test_user):
    """Test adding income without authorization - should return 401."""
    income_data = {"source_type": "Salary", "description": "Monthly salary", "annual_amount": 350000, "is_paye": True}
    response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_income_authorized(authorized_client, test_user, test_db):
    """Test adding income with authorization."""
    income_data = {"source_type": "Salary", "description": "Monthly salary", "annual_amount": 350000, "is_paye": True}
    response = authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["source_type"] == income_data["source_type"]
    assert data["annual_amount"] == income_data["annual_amount"]
    assert data["user_id"] == test_user.id


def test_calculate_tax_with_tax_data(authorized_client, test_user, test_db):
    """Test tax calculation endpoint with proper tax data setup."""
    from app.models.tax_models import (
        MedicalTaxCredit,
        TaxBracket,
        TaxRebate,
        TaxThreshold,
    )
    from app.utils.tax_utils import get_tax_year

    #Set up tax data in test database
    tax_year = get_tax_year()

    #Add basic tax bracket
    bracket = TaxBracket(lower_limit=1, upper_limit=237100, rate=0.18, base_amount=0, tax_year=tax_year)
    test_db.add(bracket)

    #Add rebate
    rebate = TaxRebate(primary=17235, secondary=9444, tertiary=3145, tax_year=tax_year)
    test_db.add(rebate)

    #Add threshold
    threshold = TaxThreshold(below_65=95750, age_65_to_74=148217, age_75_plus=165689, tax_year=tax_year)
    test_db.add(threshold)

    #Add medical credit
    medical = MedicalTaxCredit(main_member=347, additional_member=347, tax_year=tax_year)
    test_db.add(medical)
    test_db.commit()

    #Add income
    income_data = {"source_type": "Salary", "description": "Monthly salary", "annual_amount": 350000, "is_paye": True}
    authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)

    #Calculate tax
    response = authorized_client.get(f"/api/tax/users/{test_user.id}/tax-calculation/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    #validation of the response structure
    assert "gross_income" in data
    assert "taxable_income" in data
    assert "final_tax" in data
    assert data["gross_income"] == 350000


def test_calculate_provisional_tax_with_tax_data(authorized_client, test_user, test_db):
    """Test provisional tax calculation with proper setup."""
    from app.models.tax_models import (
        MedicalTaxCredit,
        TaxBracket,
        TaxRebate,
        TaxThreshold,
    )
    from app.utils.tax_utils import get_tax_year

    #Set up tax data in test database
    tax_year = get_tax_year()

    #Add basic tax bracket
    bracket = TaxBracket(lower_limit=1, upper_limit=237100, rate=0.18, base_amount=0, tax_year=tax_year)
    test_db.add(bracket)

    #Add rebate
    rebate = TaxRebate(primary=17235, secondary=9444, tertiary=3145, tax_year=tax_year)
    test_db.add(rebate)

    #Add threshold
    threshold = TaxThreshold(below_65=95750, age_65_to_74=148217, age_75_plus=165689, tax_year=tax_year)
    test_db.add(threshold)

    #Add medical credit
    medical = MedicalTaxCredit(main_member=347, additional_member=347, tax_year=tax_year)
    test_db.add(medical)
    test_db.commit()

    #Add income
    income_data = {"source_type": "Salary", "description": "Monthly salary", "annual_amount": 350000, "is_paye": True}
    authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)

    #Calculate provisional tax
    response = authorized_client.get(f"/api/tax/users/{test_user.id}/provisional-tax/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    #validation of the response structure
    assert "total_tax" in data
    assert "first_payment" in data
    assert "second_payment" in data
