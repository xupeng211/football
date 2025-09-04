"""
Tests for security models.

Simple and accurate tests for security enums and models.
"""

from datetime import datetime
from uuid import uuid4

from football_predict_system.core.security.models import (
    Permission,
    SecurityConfig,
    TokenPayload,
    User,
    UserRole,
)


class TestUserRole:
    """Test UserRole enum."""

    def test_user_role_values(self):
        """Test UserRole enum values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.GUEST.value == "guest"
        assert UserRole.API_CLIENT.value == "api_client"

    def test_user_role_equality(self):
        """Test UserRole equality with strings."""
        assert UserRole.ADMIN == "admin"
        assert UserRole.USER == "user"
        assert UserRole.GUEST == "guest"
        assert UserRole.API_CLIENT == "api_client"

    def test_user_role_iteration(self):
        """Test UserRole can be iterated."""
        roles = list(UserRole)
        assert len(roles) == 4
        assert UserRole.ADMIN in roles
        assert UserRole.USER in roles

    def test_user_role_membership(self):
        """Test UserRole membership."""
        roles = {UserRole.ADMIN, UserRole.USER}
        assert UserRole.ADMIN in roles
        assert UserRole.GUEST not in roles


class TestPermission:
    """Test Permission enum."""

    def test_prediction_permissions(self):
        """Test prediction permissions."""
        assert Permission.READ_PREDICTIONS.value == "read:predictions"
        assert Permission.CREATE_PREDICTIONS.value == "create:predictions"
        assert Permission.UPDATE_PREDICTIONS.value == "update:predictions"
        assert Permission.DELETE_PREDICTIONS.value == "delete:predictions"

    def test_model_permissions(self):
        """Test model permissions."""
        assert Permission.READ_MODELS.value == "read:models"
        assert Permission.CREATE_MODELS.value == "create:models"
        assert Permission.MODEL_TRAIN.value == "train:models"
        assert Permission.UPDATE_MODELS.value == "update:models"
        assert Permission.DELETE_MODELS.value == "delete:models"

    def test_data_permissions(self):
        """Test data permissions."""
        assert Permission.READ_USERS.value == "read:users"
        assert Permission.DATA_READ.value == "read:data"
        assert Permission.DATA_WRITE.value == "write:data"
        assert Permission.DATA_INGEST.value == "ingest:data"

    def test_admin_permissions(self):
        """Test admin permissions."""
        assert Permission.ADMIN_ACCESS.value == "admin:access"
        assert Permission.ADMIN_READ.value == "admin:read"
        assert Permission.ADMIN_WRITE.value == "admin:write"
        assert Permission.USER_MANAGE.value == "manage:users"

    def test_system_permissions(self):
        """Test system permissions."""
        assert Permission.HEALTH_CHECK.value == "system:health"
        assert Permission.METRICS_READ.value == "read:metrics"

    def test_permission_equality(self):
        """Test Permission equality with strings."""
        assert Permission.READ_PREDICTIONS == "read:predictions"
        assert Permission.ADMIN_ACCESS == "admin:access"

    def test_permission_aliases(self):
        """Test permission aliases."""
        # Check aliases exist and equal main permissions
        assert Permission.PREDICT_READ == Permission.READ_PREDICTIONS
        assert Permission.PREDICT_WRITE == Permission.CREATE_PREDICTIONS
        assert Permission.MODEL_READ == Permission.READ_MODELS
        assert Permission.MODEL_WRITE == Permission.CREATE_MODELS


class TestUser:
    """Test User model."""

    def test_user_creation_basic(self):
        """Test basic User creation."""
        user_id = uuid4()
        user = User(
            id=user_id,
            username="testuser",
            email="test@example.com",
            role=UserRole.USER,
            created_at=datetime.utcnow(),
        )

        assert user.id == user_id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.permissions == []
        assert user.is_active is True
        assert user.is_verified is False

    def test_user_with_permissions(self):
        """Test User with permissions."""
        permissions = [Permission.READ_PREDICTIONS, Permission.READ_MODELS]
        user = User(
            id=uuid4(),
            username="poweruser",
            email="power@example.com",
            role=UserRole.USER,
            permissions=permissions,
            created_at=datetime.utcnow(),
        )

        assert len(user.permissions) == 2
        assert Permission.READ_PREDICTIONS in user.permissions
        assert Permission.READ_MODELS in user.permissions

    def test_user_admin(self):
        """Test admin User."""
        user = User(
            id=uuid4(),
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN,
            permissions=[Permission.ADMIN_ACCESS],
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
        )

        assert user.role == UserRole.ADMIN
        assert user.is_active is True
        assert user.is_verified is True

    def test_user_serialization(self):
        """Test User serialization."""
        user = User(
            id=uuid4(),
            username="serialtest",
            email="serial@example.com",
            role=UserRole.API_CLIENT,
            permissions=[Permission.DATA_READ],
            is_active=False,
            created_at=datetime.utcnow(),
        )

        data = user.model_dump()

        assert data["username"] == "serialtest"
        assert data["email"] == "serial@example.com"
        assert data["role"] == "api_client"
        assert data["is_active"] is False
        assert len(data["permissions"]) == 1

    def test_user_json_serialization(self):
        """Test User JSON serialization."""
        user = User(
            id=uuid4(),
            username="jsontest",
            email="json@example.com",
            role=UserRole.GUEST,
            created_at=datetime.utcnow(),
        )

        json_data = user.model_dump_json()
        assert isinstance(json_data, str)
        assert "jsontest" in json_data
        assert "guest" in json_data

    def test_user_defaults(self):
        """Test User defaults."""
        user = User(
            id=uuid4(),
            username="defaulttest",
            email="default@example.com",
            role=UserRole.USER,
        )

        assert user.permissions == []
        assert user.is_active is True
        assert user.is_verified is False


class TestSecurityConfig:
    """Test SecurityConfig model."""

    def test_security_config_creation(self):
        """Test SecurityConfig creation."""
        config = SecurityConfig(
            jwt_secret_key="secret123",
            jwt_algorithm="HS256",
            jwt_expire_minutes=30,
            requests_per_minute=60,
            burst_size=10,
        )

        assert config.jwt_secret_key == "secret123"
        assert config.jwt_algorithm == "HS256"
        assert config.jwt_expire_minutes == 30
        assert config.requests_per_minute == 60
        assert config.burst_size == 10

    def test_security_config_defaults(self):
        """Test SecurityConfig defaults."""
        config = SecurityConfig(jwt_secret_key="secret")

        assert config.jwt_algorithm == "HS256"
        assert config.jwt_expire_minutes == 30
        assert config.requests_per_minute == 60
        assert config.burst_size == 10
        assert config.api_key_length == 32
        assert config.api_key_expire_days == 365

    def test_security_config_serialization(self):
        """Test SecurityConfig serialization."""
        config = SecurityConfig(
            jwt_secret_key="testsecret", jwt_expire_minutes=60, requests_per_minute=120
        )

        data = config.model_dump()

        assert data["jwt_secret_key"] == "testsecret"
        assert data["jwt_expire_minutes"] == 60
        assert data["requests_per_minute"] == 120

    def test_security_config_validation(self):
        """Test SecurityConfig validation."""
        # Valid config should work
        config = SecurityConfig(jwt_secret_key="valid_secret")
        assert config.jwt_secret_key == "valid_secret"


class TestTokenPayload:
    """Test TokenPayload model."""

    def test_token_payload_creation(self):
        """Test TokenPayload creation."""
        payload = TokenPayload(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            role=UserRole.USER,
            exp=1234567890,
            iat=1234567800,
        )

        assert payload.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert payload.role == UserRole.USER
        assert payload.exp == 1234567890
        assert payload.iat == 1234567800

    def test_token_payload_serialization(self):
        """Test TokenPayload serialization."""
        payload = TokenPayload(
            user_id="test-user-id", role=UserRole.ADMIN, exp=9999999999, iat=1111111111
        )

        data = payload.model_dump()

        assert data["user_id"] == "test-user-id"
        assert data["role"] == "admin"
        assert data["exp"] == 9999999999
        assert data["iat"] == 1111111111

    def test_token_payload_with_different_roles(self):
        """Test TokenPayload with different roles."""
        for role in [
            UserRole.ADMIN,
            UserRole.USER,
            UserRole.GUEST,
            UserRole.API_CLIENT,
        ]:
            payload = TokenPayload(
                user_id=f"user-{role.value}", role=role, exp=1234567890, iat=1234567800
            )
            assert payload.role == role
            assert payload.user_id == f"user-{role.value}"


class TestSecurityModelsIntegration:
    """Integration tests."""

    def test_user_with_all_roles(self):
        """Test User with all role types."""
        roles = [UserRole.ADMIN, UserRole.USER, UserRole.GUEST, UserRole.API_CLIENT]

        for role in roles:
            user = User(
                id=uuid4(),
                username=f"user_{role.value}",
                email=f"{role.value}@example.com",
                role=role,
            )
            assert user.role == role

    def test_user_with_multiple_permissions(self):
        """Test User with multiple permissions."""
        permissions = [
            Permission.READ_PREDICTIONS,
            Permission.CREATE_PREDICTIONS,
            Permission.READ_MODELS,
            Permission.DATA_READ,
        ]

        user = User(
            id=uuid4(),
            username="multiperm",
            email="multi@example.com",
            role=UserRole.USER,
            permissions=permissions,
        )

        assert len(user.permissions) == 4
        for perm in permissions:
            assert perm in user.permissions

    def test_security_roundtrip(self):
        """Test serialization roundtrip."""
        original_user = User(
            id=uuid4(),
            username="roundtrip",
            email="roundtrip@example.com",
            role=UserRole.ADMIN,
            permissions=[Permission.ADMIN_ACCESS, Permission.READ_PREDICTIONS],
            is_active=True,
            is_verified=True,
        )

        data = original_user.model_dump()
        reconstructed = User(**data)

        assert reconstructed.username == original_user.username
        assert reconstructed.role == original_user.role
        assert reconstructed.is_active == original_user.is_active

    def test_enum_values_coverage(self):
        """Test enum values coverage."""
        # Test that we can enumerate all values
        roles = list(UserRole)
        permissions = list(Permission)

        assert len(roles) == 4
        assert len(permissions) > 15  # Should have many permissions

        # Test string values work
        for role in roles:
            assert isinstance(role.value, str)
            assert len(role.value) > 0

        for perm in permissions:
            assert isinstance(perm.value, str)
            assert ":" in perm.value  # Should have namespace format
