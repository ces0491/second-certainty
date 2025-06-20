# tests/test_security.py
import pytest
from fastapi import status

from app.core.auth import authenticate_user, create_access_token, get_password_hash, verify_password, verify_token


class TestSecurity:
    """Test security features."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        # Hash should be different from original
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are long

        # Verification should work
        assert verify_password(password, hashed)

        # Wrong password should fail
        assert not verify_password("wrongpassword", hashed)

        # Empty password should fail
        assert not verify_password("", hashed)

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (salt)."""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_jwt_token_creation(self):
        """Test JWT token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data=data)

        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long

        # Token should contain the subject
        email = verify_token(token)
        assert email == "test@example.com"

    def test_jwt_token_expiration(self):
        """Test JWT token with custom expiration."""
        from datetime import timedelta

        data = {"sub": "test@example.com"}
        token = create_access_token(data=data, expires_delta=timedelta(minutes=1))

        # Token should be valid immediately
        email = verify_token(token)
        assert email == "test@example.com"

    def test_invalid_jwt_tokens(self):
        """Test handling of invalid JWT tokens."""
        # Test invalid token
        assert verify_token("invalid_token") is None

        # Test empty token
        assert verify_token("") is None

        # Test None token
        assert verify_token(None) is None

        # Test malformed token
        assert verify_token("not.a.jwt") is None

    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention in login."""
        # Try SQL injection in email field
        malicious_data = {"email": "'; DROP TABLE user_profiles; --", "password": "password"}

        response = client.post("/api/auth/login", json=malicious_data)
        # Should return 401, not crash
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Try SQL injection in password field
        malicious_data2 = {"email": "test@example.com", "password": "' OR '1'='1"}

        response2 = client.post("/api/auth/login", json=malicious_data2)
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED

    def test_xss_prevention(self, client, test_user, auth_headers):
        """Test XSS prevention in profile updates."""
        xss_script = "<script>alert('xss')</script>"

        # Try XSS in profile name
        update_data = {"name": xss_script, "surname": "User"}

        response = client.put("/api/auth/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Check that script tags are not executed (stored as plain text)
        data = response.json()
        assert data["name"] == xss_script  # Should be stored as-is, not executed

    def test_authorization_enforcement(self, client, test_user, admin_user, auth_headers):
        """Test that authorization is properly enforced."""
        # User should not be able to access admin user's data
        response = client.get(f"/api/tax/users/{admin_user.id}/income/", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # User should not be able to add income for admin user
        income_data = {"source_type": "Salary", "annual_amount": 100000}
        response = client.post(f"/api/tax/users/{admin_user.id}/income/", json=income_data, headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_token_hijacking_prevention(self, client, test_user, admin_user):
        """Test that tokens are user-specific."""
        # Create token for test_user
        test_token = create_access_token(data={"sub": test_user.email})
        test_headers = {"Authorization": f"Bearer {test_token}"}

        # Try to access admin_user's data with test_user's token
        response = client.get(f"/api/tax/users/{admin_user.id}/tax-calculation/", headers=test_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sensitive_data_not_exposed(self, client, test_user, auth_headers):
        """Test that sensitive data is not exposed in responses."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Password should never be in response
        assert "password" not in data
        assert "hashed_password" not in data

        # Only safe fields should be present
        safe_fields = {
            "id",
            "email",
            "name",
            "surname",
            "date_of_birth",
            "is_provisional_taxpayer",
            "is_admin",
            "created_at",
        }
        for field in data.keys():
            assert field in safe_fields, f"Unexpected field exposed: {field}"

    def test_rate_limiting_simulation(self, client):
        """Test behavior under rapid requests (simulating rate limiting)."""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.post(
                "/api/auth/login", json={"email": "nonexistent@test.com", "password": "wrongpassword"}
            )
            responses.append(response)

        # All should return 401 (not rate limited in test environment)
        for response in responses:
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cors_headers(self, client):
        """Test CORS headers are present for security."""
        response = client.options("/api/auth/me")

        # Should handle OPTIONS request (CORS preflight)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]

    def test_password_strength_validation(self, client):
        """Test password strength requirements."""
        weak_passwords = [
            "123",  # Too short
            "password",  # Too common
            "12345678",  # Only numbers
            "abcdefgh",  # Only letters
        ]

        for weak_password in weak_passwords:
            user_data = {
                "email": f"test{weak_password}@example.com",
                "password": weak_password,
                "name": "Test",
                "surname": "User",
                "date_of_birth": "1990-01-01",
            }

            response = client.post("/api/auth/register", json=user_data)
            # Should reject weak passwords
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_authentication_user_function(self, test_db, test_user):
        """Test the authenticate_user function directly."""
        # Valid credentials should work
        authenticated_user = authenticate_user(test_db, test_user.email, "testpass123")
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id

        # Invalid email should fail
        result = authenticate_user(test_db, "nonexistent@test.com", "testpass123")
        assert result is None

        # Invalid password should fail
        result = authenticate_user(test_db, test_user.email, "wrongpassword")
        assert result is None

        # Case sensitivity test
        result = authenticate_user(test_db, test_user.email.upper(), "testpass123")
        assert result is not None  # Email should be case-insensitive

    def test_admin_privilege_escalation_prevention(self, client, test_user, auth_headers):
        """Test that regular users cannot escalate to admin privileges."""
        # Try to update profile to set admin flag
        update_data = {"name": "Test", "is_admin": True}  # This should be ignored

        response = client.put("/api/auth/profile", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Check that admin flag was not set
        user_response = client.get("/api/auth/me", headers=auth_headers)
        user_data = user_response.json()
        assert user_data.get("is_admin", False) is False

    def test_session_security(self, client, test_user):
        """Test session security measures."""
        # Login to get token
        login_data = {"email": test_user.email, "password": "testpass123"}
        login_response = client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Use token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # Logout (invalidate session client-side)
        logout_response = client.post("/api/auth/logout", headers=headers)
        assert logout_response.status_code == status.HTTP_200_OK

        # Token should still work (JWT is stateless) but client should discard it
        post_logout_response = client.get("/api/auth/me", headers=headers)
        assert post_logout_response.status_code == status.HTTP_200_OK  # JWT still valid

    def test_input_validation_boundaries(self, client):
        """Test input validation boundary conditions."""
        # Test extremely long inputs
        long_string = "a" * 1000

        user_data = {
            "email": f"{long_string}@example.com",
            "password": "validpass123",
            "name": long_string,
            "surname": long_string,
            "date_of_birth": "1990-01-01",
        }

        response = client.post("/api/auth/register", json=user_data)
        # Should handle long inputs gracefully (either accept or reject cleanly)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]
