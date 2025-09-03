"""Security data models and enums."""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, validator


class UserRole(str, Enum):
    """User roles for authorization."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    API_CLIENT = "api_client"


class Permission(str, Enum):
    """System permissions for fine-grained access control."""

    # Predictions
    READ_PREDICTIONS = "read:predictions"
    PREDICT_READ = "read:predictions"  # Alias for compatibility
    CREATE_PREDICTIONS = "create:predictions"
    PREDICT_WRITE = "create:predictions"  # Alias for compatibility
    UPDATE_PREDICTIONS = "update:predictions"
    DELETE_PREDICTIONS = "delete:predictions"

    # Models
    READ_MODELS = "read:models"
    MODEL_READ = "read:models"  # Alias for compatibility
    CREATE_MODELS = "create:models"
    MODEL_WRITE = "create:models"  # Alias for compatibility
    MODEL_TRAIN = "train:models"
    UPDATE_MODELS = "update:models"
    DELETE_MODELS = "delete:models"

    # Data
    READ_USERS = "read:users"
    DATA_READ = "read:data"
    DATA_WRITE = "write:data"
    DATA_INGEST = "ingest:data"
    CREATE_USERS = "create:users"
    UPDATE_USERS = "update:users"
    DELETE_USERS = "delete:users"

    # Admin
    ADMIN_ACCESS = "admin:access"
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    USER_MANAGE = "manage:users"

    # System
    HEALTH_CHECK = "system:health"
    METRICS_READ = "read:metrics"


class User(BaseModel):
    """User model for authentication and authorization."""

    id: UUID
    username: str
    email: str
    role: UserRole
    permissions: list[Permission] = []
    is_active: bool = True
    is_verified: bool = False


class SecurityConfig(BaseModel):
    """Security configuration settings."""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # Rate limiting
    requests_per_minute: int = 60
    burst_size: int = 10

    # API Key settings
    api_key_length: int = 32
    api_key_expire_days: int = 365

    @validator("jwt_secret_key")
    def jwt_key_not_empty(cls, v: Any) -> str:
        if not v or v.strip() == "":
            raise ValueError("JWT secret key cannot be empty")
        return str(v)


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    user_id: str
    role: UserRole
    exp: int
    iat: int
