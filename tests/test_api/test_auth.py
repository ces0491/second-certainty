# tests/test_api/test_auth.py
import pytest
from fastapi import status


class TestAuthAPI:
    """Test the authentication API endpoints."""

    def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "name": "New",
            "surname": "User",
            "date_of_birth": "1995-05-15",
            "is_provisional_taxpayer": False
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert "message" in data
        assert "user_id" in data
        assert "User created successfully" in data["message"]

    def test_register_user_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user.email,  # Same email as test_user
            "password": "securepassword123",
            "name": "Duplicate",
            "surname": "User",
            "date_of_birth": "1995-05-15",
            "is_provisional_taxpayer": False
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "Email already registered" in data["detail"]

    def test_register_user_invalid_password(self, client):
        """Test registration with password too short."""
        user_data = {
            "email": "user@example.com",
            "password": "short",  # Too short
            "name": "Test",
            "surname": "User",
            "date_of_birth": "1995-05-15",
            "is_provisional_taxpayer": False
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_invalid_date_format(self, client):
        """Test registration with invalid date format."""
        user_data = {
            "email": "user@example.com",
            "password": "securepassword123",
            "name": "Test",
            "surname": "User",
            "date_of_birth": "invalid-date",
            "is_provisional_taxpayer": False
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_user_future_date_of_birth(self, client):
        """Test registration with future date of birth."""
        user_data = {
            "email": "user@example.com",
            "password": "securepassword123",
            "name": "Test",
            "surname": "User",
            "date_of_birth": "2030-01-01",  # Future date
            "is_provisional_taxpayer": False
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "must be in the past" in data["detail"]

    def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "email": test_user.email,
            "password": "password123"  # From test_user fixture
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email
        assert data["user"]["id"] == test_user.id

    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        data = response.json()
        assert "Incorrect email or password" in data["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_oauth2_token_endpoint(self, client, test_user):
        """Test OAuth2 compatible token endpoint."""
        form_data = {
            "username": test_user.email,  # OAuth2 uses 'username' field
            "password": "password123"
        }
        
        response = client.post("/api/auth/token", data=form_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_get_current_user(self, authorized_client, test_user):
        """Test getting current user profile."""
        response = authorized_client.get("/api/auth/me")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["surname"] == test_user.surname
        assert data["id"] == test_user.id

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authorization."""
        response = client.get("/api/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_success(self, authorized_client, test_user):
        """Test successful profile update."""
        update_data = {
            "name": "Updated",
            "surname": "Name", 
            "is_provisional_taxpayer": True
        }
        
        response = authorized_client.put("/api/auth/profile", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Updated"
        assert data["surname"] == "Name"
        assert data["is_provisional_taxpayer"] is True

    def test_update_profile_partial(self, authorized_client, test_user):
        """Test partial profile update."""
        update_data = {
            "name": "NewName"
            # Only updating name
        }
        
        response = authorized_client.put("/api/auth/profile", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "NewName"
        assert data["surname"] == test_user.surname  # Should remain unchanged

    def test_update_profile_invalid_date(self, authorized_client):
        """Test profile update with invalid date."""
        update_data = {
            "date_of_birth": "2030-01-01"  # Future date
        }
        
        response = authorized_client.put("/api/auth/profile", json=update_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_profile_unauthorized(self, client):
        """Test profile update without authorization."""
        update_data = {"name": "New Name"}
        
        response = client.put("/api/auth/profile", json=update_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_success(self, authorized_client, test_user):
        """Test successful password change."""
        password_data = {
            "current_password": "password123",
            "new_password": "newpassword123"
        }
        
        response = authorized_client.put("/api/auth/change-password", json=password_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "Password changed successfully" in data["message"]

    def test_change_password_wrong_current(self, authorized_client):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        
        response = authorized_client.put("/api/auth/change-password", json=password_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "Current password is incorrect" in data["detail"]

    def test_change_password_weak_new_password(self, authorized_client):
        """Test password change with weak new password."""
        password_data = {
            "current_password": "password123",
            "new_password": "weak"  # Too short
        }
        
        response = authorized_client.put("/api/auth/change-password", json=password_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_change_password_unauthorized(self, client):
        """Test password change without authorization."""
        password_data = {
            "current_password": "password123",
            "new_password": "newpassword123"
        }
        
        response = client.put("/api/auth/change-password", json=password_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_endpoint(self, authorized_client):
        """Test logout endpoint."""
        response = authorized_client.post("/api/auth/logout")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "Successfully logged out" in data["message"]

    def test_login_after_password_change(self, client, test_user, test_db):
        """Test login with new password after password change."""
        # First login and change password
        login_data = {
            "email": test_user.email,
            "password": "password123"
        }
        
        login_response = client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Change password
        headers = {"Authorization": f"Bearer {token}"}
        password_data = {
            "current_password": "password123",
            "new_password": "newpassword123"
        }
        
        change_response = client.put("/api/auth/change-password", json=password_data, headers=headers)
        assert change_response.status_code == status.HTTP_200_OK
        
        # Try login with new password
        new_login_data = {
            "email": test_user.email,
            "password": "newpassword123"
        }
        
        new_login_response = client.post("/api/auth/login", json=new_login_data)
        assert new_login_response.status_code == status.HTTP_200_OK
        
        # Old password should not work
        old_login_response = client.post("/api/auth/login", json=login_data)
        assert old_login_response.status_code == status.HTTP_401_UNAUTHORIZED