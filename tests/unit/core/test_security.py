"""Tests for core security module."""

from unittest.mock import patch

import pytest

from football_predict_system.core.exceptions import UnauthorizedError
from football_predict_system.core.security import (
    JWTManager,
    Permission,
    SecurityHeaders,
    User,
    UserRole,
    create_api_key,
    require_permission,
    verify_api_key,
)


class TestUserRole:
    """Test UserRole enum."""

    def test_user_roles_defined(self):
        """Test that all expected user roles are defined."""
        assert UserRole.ADMIN == "admin"
        assert UserRole.USER == "user"
        assert UserRole.READONLY == "readonly"
        assert UserRole.API_CLIENT == "api_client"


class TestPermission:
    """Test Permission enum."""

    def test_permissions_defined(self):
        """Test that key permissions are defined."""
        assert Permission.PREDICT_READ == "predict:read"
        assert Permission.PREDICT_WRITE == "predict:write"
        assert Permission.MODEL_READ == "model:read"
        assert Permission.MODEL_WRITE == "model:write"


class TestUser:
    """Test User model."""

    def test_user_creation(self):
        """Test creating a user instance."""
        user = User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            permissions=[Permission.PREDICT_READ]
        )

        assert user.id == "test-user-id"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert Permission.PREDICT_READ in user.permissions

    def test_user_has_permission(self):
        """Test user permission checking."""
        user = User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            permissions=[Permission.PREDICT_READ, Permission.MODEL_READ]
        )

        assert user.has_permission(Permission.PREDICT_READ)
        assert user.has_permission(Permission.MODEL_READ)
        assert not user.has_permission(Permission.MODEL_WRITE)


class TestAuthenticationService:
    """Test AuthenticationService."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthenticationService instance."""
        with patch('football_predict_system.core.security.get_settings') as mock_settings:
            mock_settings.return_value.jwt_secret_key = "test_secret_key"
            mock_settings.return_value.jwt_algorithm = "HS256"
            mock_settings.return_value.jwt_expire_minutes = 30
            return AuthenticationService()

    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "test_password_123"

        hashed = auth_service.hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password(self, auth_service):
        """Test password verification."""
        password = "test_password_123"

        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("wrong_password", hashed)


class TestJWTManager:
    """Test JWT Manager."""

    @pytest.fixture
    def jwt_manager(self):
        """Create JWT manager instance."""
        with patch(
            'football_predict_system.core.security.get_settings'
        ) as mock_settings:
            mock_settings.return_value.jwt_secret_key = "test_secret_key"
            mock_settings.return_value.jwt_algorithm = "HS256"
            mock_settings.return_value.jwt_expire_minutes = 30
            return JWTManager()

    def test_create_access_token(self, jwt_manager):
        """Test creating access token."""
        user_data = {"sub": "testuser", "role": "user"}

        token = jwt_manager.create_access_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self, jwt_manager):
        """Test verifying valid token."""
        user_data = {"sub": "testuser", "role": "user"}
        token = jwt_manager.create_access_token(user_data)

        payload = jwt_manager.verify_token(token)

        assert payload["sub"] == "testuser"
        assert payload["role"] == "user"

    def test_verify_token_invalid(self, jwt_manager):
        """Test verifying invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(UnauthorizedError):
            jwt_manager.verify_token(invalid_token)

    def test_create_refresh_token(self, jwt_manager):
        """Test creating refresh token."""
        user_data = {"sub": "testuser"}

        token = jwt_manager.create_refresh_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0


class TestSecurityHeaders:
    """Test SecurityHeaders."""

    def test_get_security_headers(self):
        """Test getting security headers."""
        headers = SecurityHeaders.get_security_headers()

        assert isinstance(headers, dict)
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers

        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"


class TestAPIKeyFunctions:
    """Test API key functions."""

    def test_create_api_key(self):
        """Test creating API key."""
        api_key = create_api_key()

        assert isinstance(api_key, str)
        assert len(api_key) >= 32  # Should be at least 32 characters

    @patch('football_predict_system.core.security.get_settings')
    def test_verify_api_key_valid(self, mock_settings):
        """Test verifying valid API key."""
        mock_settings.return_value.api_keys = ["valid_api_key_123"]

        result = verify_api_key("valid_api_key_123")

        assert result is True

    @patch('football_predict_system.core.security.get_settings')
    def test_verify_api_key_invalid(self, mock_settings):
        """Test verifying invalid API key."""
        mock_settings.return_value.api_keys = ["valid_api_key_123"]

        result = verify_api_key("invalid_api_key")

        assert result is False


class TestRequirePermission:
    """Test permission decorator."""

    def test_require_permission_decorator_exists(self):
        """Test that the require_permission decorator exists."""
        assert callable(require_permission)

    def test_require_permission_with_valid_permission(self):
        """Test permission decorator with valid permission."""
        # Create a mock function to decorate
        @require_permission(Permission.PREDICT_READ)
        async def test_function(user: User):
            return {"message": "success"}

        # This should not raise an exception
        assert callable(test_function)
