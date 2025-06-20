# tests/test_authentication.py
import pytest
from fastapi import status

class TestAuthentication:
    """Test authentication functionality."""
    
    def test_user_registration_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@test.com",
            "password": "strongpass123",
            "name": "New",
            "surname": "User",
            "date_of_birth": "1992-06-20",
            "is_provisional_taxpayer": False
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert "message" in data
        assert "user_id" in data
        assert data["message"] == "User created successfully"
    
    def test_registration_duplicate_email(self, client, test_user):
        """Test registration with existing email fails."""
        user_data = {
            "email": test_user.email,
            "password": "strongpass123",
            "name": "Duplicate",
            "surname": "User",
            "date_of_birth": "1992-06-20"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_registration_weak_password(self, client):
        """Test registration with weak password fails."""
        user_data = {
            "email": "weak@test.com",
            "password": "123",  # Too short
            "name": "Weak",
            "surname": "Password",
            "date_of_birth": "1992-06-20"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_registration_future_birth_date(self, client):
        """Test registration with future birth date fails."""
        user_data = {
            "email": "future@test.com",
            "password": "strongpass123",
            "name": "Future",
            "surname": "Born",
            "date_of_birth": "2030-01-01"  # Future date
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "must be in the past" in response.json()["detail"]
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails."""
        login_data = {
            "email": "nobody@test.com",
            "password": "somepassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user(self, client, test_user, auth_headers):
        """Test getting current user profile."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["id"] == test_user.id
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile(self, client, test_user, auth_headers):
        """Test updating user profile."""
        update_data = {
            "name": "Updated",
            "is_provisional_taxpayer": False
        }
        
        response = client.put("/api/auth/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Updated"
        assert data["is_provisional_taxpayer"] is False
    
    def test_change_password(self, client, test_user, auth_headers):
        """Test password change."""
        password_data = {
            "current_password": "testpass123",
            "new_password": "newtestpass123"
        }
        
        response = client.put("/api/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify old password no longer works
        login_data = {"email": test_user.email, "password": "testpass123"}
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Verify new password works
        new_login_data = {"email": test_user.email, "password": "newtestpass123"}
        new_login_response = client.post("/api/auth/login", json=new_login_data)
        assert new_login_response.status_code == status.HTTP_200_OK
    
    def test_oauth2_token_endpoint(self, client, test_user):
        """Test OAuth2 compatible token endpoint."""
        form_data = {
            "username": test_user.email,  # OAuth2 uses 'username' field
            "password": "testpass123"
        }
        
        response = client.post("/api/auth/token", data=form_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newtestpass123"
        }
        
        response = client.put("/api/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "Current password is incorrect" in data["detail"]
    
    def test_logout_endpoint(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "Successfully logged out" in data["message"]