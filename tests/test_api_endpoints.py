# tests/test_api_endpoints.py
import pytest
from fastapi import status


class TestTaxAPI:
    """Test tax calculation API endpoints."""

    def test_get_tax_brackets(self, client, complete_tax_data):
        """Test retrieving tax brackets."""
        response = client.get("/api/tax/tax-brackets/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 7
        assert data[0]["rate"] == 0.18
        assert data[-1]["rate"] == 0.45

    def test_get_deductible_expense_types(self, client, complete_tax_data):
        """Test retrieving deductible expense types."""
        response = client.get("/api/tax/deductible-expenses/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) >= 3  # Should have at least the 3 we created

        # Check that we have the expected expense types
        expense_names = [expense["name"] for expense in data]
        assert "Retirement Annuity" in expense_names
        assert "Medical Expenses" in expense_names
        assert "Donations" in expense_names

    def test_add_income_unauthorized(self, client, test_user):
        """Test adding income without authorization."""
        income_data = {"source_type": "Salary", "annual_amount": 350000, "is_paye": True}

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_income_authorized(self, client, test_user, auth_headers):
        """Test adding income with authorization."""
        income_data = {
            "source_type": "Salary",
            "description": "Monthly salary",
            "annual_amount": 350000,
            "is_paye": True,
        }

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["source_type"] == "Salary"
        assert data["annual_amount"] == 350000
        assert data["user_id"] == test_user.id

    def test_add_income_wrong_user(self, client, test_user, admin_user, auth_headers):
        """Test users cannot add income for other users."""
        income_data = {"source_type": "Salary", "annual_amount": 350000}

        response = client.post(f"/api/tax/users/{admin_user.id}/income/", json=income_data, headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_income(self, client, test_user, auth_headers):
        """Test retrieving user income."""
        # First add income
        income_data = {"source_type": "Salary", "annual_amount": 350000, "is_paye": True}
        client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)

        # Now retrieve it
        response = client.get(f"/api/tax/users/{test_user.id}/income/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 1
        assert data[0]["source_type"] == "Salary"

    def test_delete_income(self, client, test_user, auth_headers):
        """Test deleting income source."""
        # Add income
        income_data = {"source_type": "Salary", "annual_amount": 350000}
        add_response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        income_id = add_response.json()["id"]

        # Delete it
        delete_response = client.delete(f"/api/tax/users/{test_user.id}/income/{income_id}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's gone
        get_response = client.get(f"/api/tax/users/{test_user.id}/income/", headers=auth_headers)
        assert len(get_response.json()) == 0

    def test_add_expense_authorized(self, client, test_user, auth_headers, complete_tax_data):
        """Test adding expense with authorization."""
        expense_data = {
            "expense_type_id": 1,  # First expense type from setup
            "description": "Monthly retirement contribution",
            "amount": 5000,
        }
        response = client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["expense_type_id"] == expense_data["expense_type_id"]
        assert data["amount"] == expense_data["amount"]
        assert data["user_id"] == test_user.id

    def test_get_user_expenses(self, client, test_user, auth_headers, complete_tax_data):
        """Test retrieving user expenses."""
        # First add an expense
        expense_data = {"expense_type_id": 1, "description": "Monthly retirement contribution", "amount": 5000}
        client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data, headers=auth_headers)

        # Now retrieve it
        response = client.get(f"/api/tax/users/{test_user.id}/expenses/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["amount"] == 5000

    def test_delete_expense(self, client, test_user, auth_headers, complete_tax_data):
        """Test deleting expense."""
        # Add expense
        expense_data = {"expense_type_id": 1, "description": "Monthly retirement contribution", "amount": 5000}
        add_response = client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data, headers=auth_headers)
        expense_id = add_response.json()["id"]

        # Delete it
        delete_response = client.delete(f"/api/tax/users/{test_user.id}/expenses/{expense_id}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's gone
        get_response = client.get(f"/api/tax/users/{test_user.id}/expenses/", headers=auth_headers)
        assert len(get_response.json()) == 0

    def test_calculate_tax_complete(self, client, test_user, auth_headers, complete_tax_data):
        """Test complete tax calculation."""
        # Add income
        income_data = {"source_type": "Salary", "annual_amount": 400000, "is_paye": True}
        client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)

        # Calculate tax
        response = client.get(f"/api/tax/users/{test_user.id}/tax-calculation/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        required_fields = [
            "gross_income",
            "taxable_income",
            "tax_before_rebates",
            "rebates",
            "medical_credits",
            "final_tax",
            "effective_tax_rate",
            "monthly_tax_rate",
        ]
        for field in required_fields:
            assert field in data

        assert data["gross_income"] == 400000
        assert data["final_tax"] > 0

    def test_custom_tax_calculation(self, client, test_user, auth_headers, complete_tax_data):
        """Test custom tax calculation scenario."""
        calculation_data = {"income": 500000, "age": 40, "expenses": {"retirement": 60000, "medical": 20000}}

        response = client.post(
            f"/api/tax/users/{test_user.id}/custom-tax-calculation/", json=calculation_data, headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["gross_income"] == 500000
        assert data["taxable_income"] == 420000  # 500k - 80k expenses
        assert data["final_tax"] > 0

    def test_provisional_tax_calculation_api(self, client, test_user, auth_headers, complete_tax_data):
        """Test provisional tax calculation via API."""
        # Add income for provisional taxpayer
        income_data = {"source_type": "Consulting", "annual_amount": 500000, "is_paye": False}
        client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)

        # Calculate provisional tax
        response = client.get(f"/api/tax/users/{test_user.id}/provisional-tax/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        required_fields = ["total_tax", "taxable_income", "effective_tax_rate", "first_payment", "second_payment"]
        for field in required_fields:
            assert field in data

        # Check payment structure
        assert "amount" in data["first_payment"]
        assert "due_date" in data["first_payment"]
        assert "amount" in data["second_payment"]
        assert "due_date" in data["second_payment"]

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "database" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "app_name" in data
        assert "version" in data
        assert "message" in data

    def test_invalid_user_id_access(self, client, auth_headers):
        """Test accessing endpoints with invalid user ID."""
        # Try to access non-existent user's data
        response = client.get("/api/tax/users/99999/tax-calculation/", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_tax_calculation_with_expenses(self, client, test_user, auth_headers, complete_tax_data):
        """Test tax calculation including expenses."""
        # Add income
        income_data = {"source_type": "Salary", "annual_amount": 500000, "is_paye": True}
        client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)

        # Add expense
        expense_data = {
            "expense_type_id": 1,  # Retirement contribution
            "description": "Annual RA contribution",
            "amount": 75000,
        }
        client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data, headers=auth_headers)

        # Calculate tax
        response = client.get(f"/api/tax/users/{test_user.id}/tax-calculation/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["gross_income"] == 500000
        assert data["taxable_income"] == 425000  # 500k - 75k expense
        assert data["final_tax"] > 0
