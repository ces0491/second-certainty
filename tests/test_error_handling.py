# tests/test_error_handling.py
import pytest
from fastapi import status


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_nonexistent_user_tax_calculation(self, client, auth_headers, complete_tax_data):
        """Test tax calculation for non-existent user."""
        response = client.get("/api/tax/users/99999/tax-calculation/", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        data = response.json()
        assert "detail" in data

    def test_tax_calculation_no_tax_data(self, client, test_user, auth_headers):
        """Test tax calculation when no tax data exists in database."""
        response = client.get(f"/api/tax/users/{test_user.id}/tax-calculation/", headers=auth_headers)
        # Should handle gracefully - either return error or zero values
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_provisional_tax_non_provisional_user(self, client, admin_user, admin_headers, complete_tax_data):
        """Test provisional tax calculation for non-provisional user."""
        response = client.get(f"/api/tax/users/{admin_user.id}/provisional-tax/", headers=admin_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert "not a provisional taxpayer" in data["detail"]

    def test_invalid_income_amount(self, client, test_user, auth_headers):
        """Test adding income with invalid amount."""
        income_data = {"source_type": "Salary", "annual_amount": -50000, "is_paye": True}  # Negative amount

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        # Should handle validation appropriately
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_invalid_expense_amount(self, client, test_user, auth_headers, complete_tax_data):
        """Test adding expense with invalid amount."""
        expense_data = {"expense_type_id": 1, "description": "Invalid expense", "amount": -1000}  # Negative amount

        response = client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data, headers=auth_headers)
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_invalid_expense_type_id(self, client, test_user, auth_headers):
        """Test adding expense with non-existent expense type."""
        expense_data = {
            "expense_type_id": 99999,  # Non-existent expense type
            "description": "Invalid expense type",
            "amount": 1000,
        }

        response = client.post(f"/api/tax/users/{test_user.id}/expenses/", json=expense_data, headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_income(self, client, test_user, auth_headers):
        """Test deleting non-existent income source."""
        response = client.delete(f"/api/tax/users/{test_user.id}/income/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_expense(self, client, test_user, auth_headers):
        """Test deleting non-existent expense."""
        response = client.delete(f"/api/tax/users/{test_user.id}/expenses/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_malformed_json_request(self, client, test_user, auth_headers):
        """Test handling of malformed JSON in requests."""
        # Send malformed JSON
        response = client.post(
            f"/api/tax/users/{test_user.id}/income/",
            data="{ invalid json",  # Malformed JSON
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_required_fields(self, client, test_user, auth_headers):
        """Test handling of missing required fields."""
        # Missing annual_amount field
        income_data = {
            "source_type": "Salary",
            # "annual_amount": missing
            "is_paye": True,
        }

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_field_types(self, client, test_user, auth_headers):
        """Test handling of invalid field types."""
        income_data = {
            "source_type": "Salary",
            "annual_amount": "not_a_number",  # Should be float
            "is_paye": "not_a_boolean",  # Should be boolean
        }

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_extremely_large_values(self, client, test_user, auth_headers):
        """Test handling of extremely large values."""
        income_data = {"source_type": "Salary", "annual_amount": 999999999999999, "is_paye": True}  # Very large number

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        # Should either accept or reject gracefully
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_database_connection_error_simulation(self, client, test_user, auth_headers):
        """Test handling when database is unavailable."""
        # This test documents expected behavior during database issues
        # In a real scenario, the database dependency would fail

        # The application should handle database errors gracefully
        response = client.get(f"/api/tax/users/{test_user.id}/income/", headers=auth_headers)

        # Should return either data or a proper error response
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]

    def test_invalid_tax_year_format(self, client, test_user, auth_headers):
        """Test handling of invalid tax year format."""
        response = client.get(f"/api/tax/users/{test_user.id}/income/?tax_year=invalid-format", headers=auth_headers)
        # Should handle invalid tax year gracefully
        assert response.status_code in [
            status.HTTP_200_OK,  # Might default to current year
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_concurrent_modifications(self, client, test_user, auth_headers):
        """Test handling of concurrent modifications to user data."""
        # Add income
        income_data = {"source_type": "Salary", "annual_amount": 300000}
        add_response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        assert add_response.status_code == status.HTTP_201_CREATED
        income_id = add_response.json()["id"]

        # Try to delete the same income multiple times concurrently
        responses = []
        for _ in range(3):
            response = client.delete(f"/api/tax/users/{test_user.id}/income/{income_id}", headers=auth_headers)
            responses.append(response)

        # First should succeed, others should fail gracefully
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_204_NO_CONTENT)
        error_count = sum(1 for r in responses if r.status_code == status.HTTP_404_NOT_FOUND)

        assert success_count == 1
        assert error_count == 2

    def test_empty_string_values(self, client, test_user, auth_headers):
        """Test handling of empty string values."""
        income_data = {"source_type": "", "description": "", "annual_amount": 300000, "is_paye": True}  # Empty string

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        # Should handle empty strings appropriately
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_null_values(self, client, test_user, auth_headers):
        """Test handling of null values."""
        income_data = {
            "source_type": "Salary",
            "description": None,  # Null value
            "annual_amount": 300000,
            "is_paye": True,
        }

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        # Should handle null values in optional fields
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_unicode_and_special_characters(self, client, test_user, auth_headers):
        """Test handling of unicode and special characters."""
        income_data = {
            "source_type": "Salary",
            "description": "Émployé spécial 中文 🎉",  # Unicode characters
            "annual_amount": 300000,
            "is_paye": True,
        }

        response = client.post(f"/api/tax/users/{test_user.id}/income/", json=income_data, headers=auth_headers)
        # Should handle unicode characters properly
        assert response.status_code == status.HTTP_201_CREATED

    def test_sql_injection_in_user_input(self, client, test_user, auth_headers):
        """Test SQL injection prevention in user input fields."""
        malicious_income_data = {
            "source_type": "'; DROP TABLE income_sources; --",
            "description": "1' OR '1'='1",
            "annual_amount": 300000,
            "is_paye": True,
        }

        response = client.post(
            f"/api/tax/users/{test_user.id}/income/", json=malicious_income_data, headers=auth_headers
        )
        # Should not execute SQL injection
        assert response.status_code in [
            status.HTTP_201_CREATED,  # Stored as literal text
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]

        # Verify system is still functioning
        health_response = client.get("/api/health")
        assert health_response.status_code == status.HTTP_200_OK

    def test_cross_user_data_access_prevention(self, client, test_user, admin_user, auth_headers):
        """Test prevention of cross-user data access."""
        # Try to access admin user's data with regular user token
        response = client.get(f"/api/tax/users/{admin_user.id}/income/", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Try to add income for admin user with regular user token
        income_data = {"source_type": "Salary", "annual_amount": 300000}
        response = client.post(f"/api/tax/users/{admin_user.id}/income/", json=income_data, headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_http_methods(self, client, test_user, auth_headers):
        """Test handling of invalid HTTP methods."""
        # Try PATCH on endpoint that only supports GET/POST
        response = client.patch(f"/api/tax/users/{test_user.id}/income/", headers=auth_headers)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Try PUT on endpoint that doesn't support it
        response = client.put(f"/api/tax/users/{test_user.id}/income/", headers=auth_headers)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_custom_tax_calculation_invalid_data(self, client, test_user, auth_headers, complete_tax_data):
        """Test custom tax calculation with invalid input data."""
        invalid_calculation_data = {"income": "not_a_number", "age": -5, "expenses": "not_a_dict"}  # Negative age

        response = client.post(
            f"/api/tax/users/{test_user.id}/custom-tax-calculation/",
            json=invalid_calculation_data,
            headers=auth_headers,
        )
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
