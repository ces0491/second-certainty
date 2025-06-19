# tests/test_api/test_tax_calculator.py
import pytest
from fastapi import status


class TestTaxCalculatorAPI:
    """Test the tax calculator API endpoints."""

    def test_get_tax_brackets_unauthorized(self, client):
        """Test that tax brackets can be accessed without authentication."""
        response = client.get("/api/tax/tax-brackets/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_tax_brackets_with_data(self, client, tax_data_setup):
        """Test retrieving tax brackets with actual data."""
        response = client.get("/api/tax/tax-brackets/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7  # Should have 7 tax brackets
        
        # Check first bracket
        first_bracket = data[0]
        assert first_bracket["lower_limit"] == 1
        assert first_bracket["upper_limit"] == 237100
        assert first_bracket["rate"] == 0.18
        assert first_bracket["base_amount"] == 0

    def test_get_deductible_expense_types(self, client, expense_types_setup):
        """Test retrieving deductible expense types."""
        response = client.get("/api/tax/deductible-expenses/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3  # Should have 3 expense types from setup
        
        # Check that we have the expected expense types
        expense_names = [expense["name"] for expense in data]
        assert "Retirement Annuity Contributions" in expense_names
        assert "Medical Expenses" in expense_names
        assert "Donations" in expense_names

    def test_add_income_unauthorized(self, client, test_user):
        """Test adding income without authorization returns 401."""
        income_data = {
            "source_type": "Salary",
            "description": "Monthly salary",
            "annual_amount": 350000,
            "is_paye": True
        }
        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_income_authorized(self, authorized_client, test_user):
        """Test adding income with proper authorization."""
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
        assert data["is_paye"] == income_data["is_paye"]

    def test_add_income_wrong_user(self, authorized_client, test_admin_user):
        """Test that users can't add income for other users."""
        income_data = {
            "source_type": "Salary", 
            "description": "Monthly salary",
            "annual_amount": 350000,
            "is_paye": True
        }
        # Try to add income for admin user while logged in as test_user
        response = authorized_client.post(f"/api/tax/users/{test_admin_user.id}/income/", json=income_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_income(self, authorized_client, test_user):
        """Test retrieving user income sources."""
        # First add some income
        income_data = {
            "source_type": "Salary",
            "description": "Monthly salary", 
            "annual_amount": 350000,
            "is_paye": True
        }
        authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
        
        # Now retrieve it
        response = authorized_client.get(f"/api/tax/users/{test_user.id}/income/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["source_type"] == "Salary"
        assert data[0]["annual_amount"] == 350000

    def test_delete_income(self, authorized_client, test_user):
        """Test deleting income source."""
        # First add income
        income_data = {
            "source_type": "Salary",
            "description": "Monthly salary",
            "annual_amount": 350000,
            "is_paye": True
        }
        add_response = authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
        income_id = add_response.json()["id"]
        
        # Now delete it
        delete_response = authorized_client.delete(f"/api/tax/users/{test_user.id}/income/{income_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's gone
        get_response = authorized_client.get(f"/api/tax/users/{test_user.id}/income/")
        assert len(get_response.json()) == 0

    def test_add_expense_authorized(self, authorized_client, test_user, expense_types_setup):
        """Test adding expense with proper authorization."""
        expense_data = {
            "expense_type_id": 1,  # First expense type from setup
            "description": "Monthly retirement contribution",
            "amount": 5000
        }
        response = authorized_client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["expense_type_id"] == expense_data["expense_type_id"]
        assert data["amount"] == expense_data["amount"]
        assert data["user_id"] == test_user.id

    def test_get_user_expenses(self, authorized_client, test_user, expense_types_setup):
        """Test retrieving user expenses."""
        # First add an expense
        expense_data = {
            "expense_type_id": 1,
            "description": "Monthly retirement contribution",
            "amount": 5000
        }
        authorized_client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data)
        
        # Now retrieve it
        response = authorized_client.get(f"/api/tax/users/{test_user.id}/expenses/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["amount"] == 5000

    def test_calculate_tax_with_complete_setup(self, authorized_client, test_user, tax_data_setup):
        """Test tax calculation with complete tax data setup."""
        # Add income first
        income_data = {
            "source_type": "Salary",
            "description": "Annual salary",
            "annual_amount": 350000,
            "is_paye": True
        }
        authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
        
        # Calculate tax
        response = authorized_client.get(f"/api/tax/users/{test_user.id}/tax-calculation/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        # Verify response structure
        required_fields = [
            "gross_income", "taxable_income", "tax_before_rebates",
            "rebates", "medical_credits", "final_tax",
            "effective_tax_rate", "monthly_tax_rate"
        ]
        for field in required_fields:
            assert field in data
        
        assert data["gross_income"] == 350000
        assert data["taxable_income"] == 350000  # No expenses
        assert data["final_tax"] >= 0

    def test_calculate_provisional_tax(self, authorized_client, test_user, tax_data_setup):
        """Test provisional tax calculation for provisional taxpayer."""
        # Add income
        income_data = {
            "source_type": "Consulting",
            "description": "Freelance consulting",
            "annual_amount": 500000,
            "is_paye": False
        }
        authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
        
        # Calculate provisional tax
        response = authorized_client.get(f"/api/tax/users/{test_user.id}/provisional-tax/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        required_fields = [
            "total_tax", "taxable_income", "effective_tax_rate",
            "first_payment", "second_payment"
        ]
        for field in required_fields:
            assert field in data
        
        # Check payment structure
        assert "amount" in data["first_payment"]
        assert "due_date" in data["first_payment"]
        assert "amount" in data["second_payment"]
        assert "due_date" in data["second_payment"]
        
        # Payments should be roughly equal (50% each)
        total_payments = data["first_payment"]["amount"] + data["second_payment"]["amount"]
        assert abs(total_payments - data["total_tax"]) < 1  # Allow for rounding

    def test_calculate_provisional_tax_non_provisional_user(self, authorized_client, test_admin_user, tax_data_setup):
        """Test that non-provisional taxpayers get error for provisional tax calculation."""
        # Admin user is not a provisional taxpayer
        response = authorized_client.get(f"/api/tax/users/{test_admin_user.id}/provisional-tax/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_custom_tax_calculation(self, authorized_client, test_user, tax_data_setup):
        """Test custom tax calculation endpoint."""
        calculation_data = {
            "income": 400000,
            "age": 35,
            "expenses": {
                "retirement": 50000,
                "medical": 10000
            }
        }
        
        response = authorized_client.post(
            f"/api/tax/users/{test_user.id}/custom-tax-calculation/",
            json=calculation_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["gross_income"] == 400000
        assert data["taxable_income"] == 340000  # 400000 - 60000 expenses
        assert data["final_tax"] >= 0

    def test_calculate_tax_no_income(self, authorized_client, test_user, tax_data_setup):
        """Test tax calculation with no income sources."""
        response = authorized_client.get(f"/api/tax/users/{test_user.id}/tax-calculation/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["gross_income"] == 0
        assert data["taxable_income"] == 0
        assert data["final_tax"] == 0

    def test_calculate_tax_with_expenses(self, authorized_client, test_user, tax_data_setup, expense_types_setup):
        """Test tax calculation with income and expenses."""
        # Add income
        income_data = {
            "source_type": "Salary",
            "annual_amount": 400000,
            "is_paye": True
        }
        authorized_client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
        
        # Add expense
        expense_data = {
            "expense_type_id": 1,  # Retirement contribution
            "description": "Annual retirement contribution",
            "amount": 50000
        }
        authorized_client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data)
        
        # Calculate tax
        response = authorized_client.get(f"/api/tax/users/{test_user.id}/tax-calculation/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["gross_income"] == 400000
        assert data["taxable_income"] == 350000  # 400000 - 50000 expense
        assert data["final_tax"] >= 0

    def test_invalid_user_access(self, authorized_client):
        """Test accessing non-existent user returns 404."""
        response = authorized_client.get("/api/tax/users/99999/tax-calculation/")
        # This should return 403 because the user ID doesn't match the authenticated user
        assert response.status_code == status.HTTP_403_FORBIDDEN