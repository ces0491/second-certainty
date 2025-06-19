# tests/test_api/test_admin.py
import pytest
from fastapi import status
from unittest.mock import patch, MagicMock


class TestAdminAPI:
    """Test the admin API endpoints."""

    def test_update_tax_data_admin_success(self, admin_client):
        """Test successful tax data update by admin."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Tax data updated successfully",
                stderr=""
            )
            
            response = admin_client.post("/api/admin/update-tax-data")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert "Tax data update initiated" in data["message"]
            assert data["force"] is False
            assert data["year"] == "current"

    def test_update_tax_data_admin_with_force(self, admin_client):
        """Test tax data update with force flag."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Tax data updated successfully",
                stderr=""
            )
            
            response = admin_client.post("/api/admin/update-tax-data?force=true")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["force"] is True

    def test_update_tax_data_admin_with_year(self, admin_client):
        """Test tax data update with specific year."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Tax data updated successfully",
                stderr=""
            )
            
            response = admin_client.post("/api/admin/update-tax-data?year=2023-2024")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["year"] == "2023-2024"

    def test_update_tax_data_non_admin_user(self, authorized_client):
        """Test that non-admin users cannot update tax data."""
        response = authorized_client.post("/api/admin/update-tax-data")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        data = response.json()
        assert "Only administrators can update tax data" in data["detail"]

    def test_update_tax_data_unauthorized(self, client):
        """Test tax data update without authentication."""
        response = client.post("/api/admin/update-tax-data")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_tax_data_script_failure(self, admin_client):
        """Test handling of script execution failure."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Script failed to execute"
            )
            
            # The endpoint should still return success since it runs in background
            response = admin_client.post("/api/admin/update-tax-data")
            assert response.status_code == status.HTTP_200_OK
            
            # The actual failure would be logged but not returned to the client
            # since it's a background task

    def test_update_tax_data_with_all_parameters(self, admin_client):
        """Test tax data update with all parameters."""
        with patch('app.api.routes.admin.subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Tax data updated successfully",
                stderr=""
            )
            
            response = admin_client.post("/api/admin/update-tax-data?force=true&year=2024-2025")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["force"] is True
            assert data["year"] == "2024-2025"

    @patch('app.api.routes.admin.run_tax_data_update')
    def test_background_task_execution(self, mock_run_task, admin_client):
        """Test that the update runs as a background task."""
        # Make a request
        response = admin_client.post("/api/admin/update-tax-data?force=true&year=2024-2025")
        assert response.status_code == status.HTTP_200_OK
        
        # The background task should be scheduled but we can't easily test its execution in a unit test.
        # This test verifies the response structure.
        data = response.json()
        assert "Tax data update initiated" in data["message"]
