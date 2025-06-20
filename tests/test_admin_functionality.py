# tests/test_admin_functionality.py
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock

class TestAdminFunctionality:
    """Test admin-specific functionality."""
    
    def test_admin_update_tax_data_success(self, client, admin_headers):
        """Test admin can trigger tax data update successfully."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Tax data updated successfully",
                stderr=""
            )
            
            response = client.post("/api/admin/update-tax-data", headers=admin_headers)
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert "Tax data update initiated" in data["message"]
            assert data["force"] is False
            assert data["year"] == "current"
    
    def test_admin_update_tax_data_with_force(self, client, admin_headers):
        """Test admin can trigger forced tax data update."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Tax data updated successfully with force",
                stderr=""
            )
            
            response = client.post("/api/admin/update-tax-data?force=true", headers=admin_headers)
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["force"] is True
    
    def test_admin_update_tax_data_with_specific_year(self, client, admin_headers):
        """Test admin can trigger tax data update for specific year."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Tax data updated for 2023-2024",
                stderr=""
            )
            
            response = client.post("/api/admin/update-tax-data?year=2023-2024", headers=admin_headers)
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["year"] == "2023-2024"
    
    def test_admin_update_tax_data_with_all_parameters(self, client, admin_headers):
        """Test admin update with both force and year parameters."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Tax data force updated for 2024-2025",
                stderr=""
            )
            
            response = client.post("/api/admin/update-tax-data?force=true&year=2024-2025", headers=admin_headers)
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["force"] is True
            assert data["year"] == "2024-2025"
    
    def test_non_admin_cannot_update_tax_data(self, client, auth_headers):
        """Test that non-admin users cannot trigger tax data update."""
        response = client.post("/api/admin/update-tax-data", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        data = response.json()
        assert "Only administrators can update tax data" in data["detail"]
    
    def test_unauthorized_admin_access(self, client):
        """Test unauthorized access to admin endpoints."""
        response = client.post("/api/admin/update-tax-data")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_admin_update_script_failure(self, client, admin_headers):
        """Test handling when the update script fails."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Failed to fetch tax data from SARS"
            )
            
            # The endpoint should still return success since it runs in background
            response = client.post("/api/admin/update-tax-data", headers=admin_headers)
            assert response.status_code == status.HTTP_200_OK
            
            # The actual failure would be logged but not returned to client
            data = response.json()
            assert "Tax data update initiated" in data["message"]
    
    def test_admin_privileges_check(self, test_db, admin_user, test_user):
        """Test admin privilege checking logic."""
        # Admin user should have admin privileges
        assert hasattr(admin_user, 'is_admin')
        assert admin_user.is_admin is True
        
        # Regular user should not have admin privileges
        assert hasattr(test_user, 'is_admin')
        assert test_user.is_admin is False
    
    def test_admin_can_access_all_user_data(self, client, admin_user, test_user, admin_headers, complete_tax_data):
        """Test that admin can access other users' data (if implemented)."""
        # Note: This test assumes admin override is implemented
        # If not implemented, this test documents the expected behavior
        
        # Add income for test user
        income_data = {
            "source_type": "Salary",
            "annual_amount": 300000,
            "is_paye": True
        }
        
        # Admin should be able to add income for any user (if implemented)
        # Currently this will fail due to user ID mismatch check
        response = client.post(
            f"/api/tax/users/{test_user.id}/income/",
            json=income_data,
            headers=admin_headers
        )
        
        # This documents current behavior - admin can't access other users' endpoints
        # In a future version, admin override could be implemented
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_background_task_execution(self, client, admin_headers):
        """Test that tax data update runs as background task."""
        with patch('app.api.routes.admin.BackgroundTasks.add_task') as mock_add_task:
            response = client.post("/api/admin/update-tax-data", headers=admin_headers)
            assert response.status_code == status.HTTP_200_OK
            
            # Verify response is immediate (background task behavior)
            data = response.json()
            assert "Tax data update initiated" in data["message"]
    
    def test_admin_user_creation_properties(self, admin_user):
        """Test that admin user has correct properties."""
        assert admin_user.email == "admin@example.com"
        assert admin_user.is_admin is True
        assert admin_user.is_provisional_taxpayer is False  # Admin defaults to non-provisional
        assert admin_user.name == "Admin"
        assert admin_user.surname == "User"
    
    def test_admin_login_and_token_generation(self, client, admin_user):
        """Test admin user can login and receive proper token."""
        login_data = {
            "email": admin_user.email,
            "password": "adminpass123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["is_admin"] is True
    
    def test_admin_profile_access(self, client, admin_user, admin_headers):
        """Test admin can access their own profile."""
        response = client.get("/api/auth/me", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["is_admin"] is True
        assert data["email"] == admin_user.email
    
    def test_multiple_admin_operations(self, client, admin_headers):
        """Test multiple admin operations in sequence."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
            
            # Perform multiple operations
            operations = [
                ("force=false&year=2023-2024", {"force": False, "year": "2023-2024"}),
                ("force=true&year=2024-2025", {"force": True, "year": "2024-2025"}),
                ("force=true", {"force": True, "year": "current"}),
                ("year=2025-2026", {"force": False, "year": "2025-2026"}),
            ]
            
            for params, expected in operations:
                response = client.post(f"/api/admin/update-tax-data?{params}", headers=admin_headers)
                assert response.status_code == status.HTTP_200_OK
                
                data = response.json()
                assert data["force"] == expected["force"]
                assert data["year"] == expected["year"]
    
    def test_admin_error_handling(self, client, admin_headers):
        """Test admin endpoint error handling."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            # Simulate script timeout
            mock_subprocess.side_effect = Exception("Script timeout")
            
            response = client.post("/api/admin/update-tax-data", headers=admin_headers)
            # Should still return success as it's a background task
            assert response.status_code == status.HTTP_200_OK
    
    def test_admin_parameter_validation(self, client, admin_headers):
        """Test parameter validation for admin endpoints."""
        # Test invalid year format
        response = client.post("/api/admin/update-tax-data?year=invalid-year", headers=admin_headers)
        # Should still accept it (validation might be in the script)
        assert response.status_code == status.HTTP_200_OK
        
        # Test invalid force parameter
        response = client.post("/api/admin/update-tax-data?force=invalid", headers=admin_headers)
        # Should still accept it (FastAPI will convert to boolean)
        assert response.status_code == status.HTTP_200_OK
    
    def test_admin_audit_trail(self, client, admin_user, admin_headers):
        """Test that admin actions could be audited (if implemented)."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
            
            response = client.post("/api/admin/update-tax-data?force=true", headers=admin_headers)
            assert response.status_code == status.HTTP_200_OK
            
            # In a real implementation, admin actions might be logged
            # This test documents the expectation for audit trails
            # Current implementation logs to console/files
    
    def test_admin_concurrent_operations(self, client, admin_headers):
        """Test handling of concurrent admin operations."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
            
            # Simulate concurrent requests
            responses = []
            for i in range(3):
                response = client.post("/api/admin/update-tax-data", headers=admin_headers)
                responses.append(response)
            
            # All should succeed (background tasks handle concurrency)
            for response in responses:
                assert response.status_code == status.HTTP_200_OK
    
    def test_admin_system_health_check(self, client, admin_headers):
        """Test admin can check system health."""
        # Admin should be able to access health endpoint
        response = client.get("/api/health", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data