"""
Production-grade security and authentication system.

This module provides:
- JWT-based authentication
- Role-based authorization
- Rate limiting
- Security headers
- Input validation and sanitization
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

import bcrypt
import jwt
from pydantic import BaseModel, validator

from .config import get_settings
from .exceptions import ForbiddenError, UnauthorizedError, ValidationError
from .logging import get_logger

logger = get_logger(__name__)


class UserRole(str, Enum):
    """User roles for authorization."""

    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    API_CLIENT = "api_client"


class Permission(str, Enum):
    """System permissions."""

    # Prediction permissions
    PREDICT_READ = "predict:read"
    PREDICT_WRITE = "predict:write"

    # Model permissions
    MODEL_READ = "model:read"
    MODEL_WRITE = "model:write"
    MODEL_TRAIN = "model:train"

    # Data permissions
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_INGEST = "data:ingest"

    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    USER_MANAGE = "user:manage"

    # System permissions
    HEALTH_CHECK = "system:health"
    METRICS_READ = "system:metrics"


# Role-based permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        Permission.PREDICT_READ,
        Permission.PREDICT_WRITE,
        Permission.MODEL_READ,
        Permission.MODEL_WRITE,
        Permission.MODEL_TRAIN,
        Permission.DATA_READ,
        Permission.DATA_WRITE,
        Permission.DATA_INGEST,
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.USER_MANAGE,
        Permission.HEALTH_CHECK,
        Permission.METRICS_READ,
    },
    UserRole.USER: {
        Permission.PREDICT_READ,
        Permission.PREDICT_WRITE,
        Permission.MODEL_READ,
        Permission.DATA_READ,
        Permission.HEALTH_CHECK,
    },
    UserRole.READONLY: {
        Permission.PREDICT_READ,
        Permission.MODEL_READ,
        Permission.DATA_READ,
        Permission.HEALTH_CHECK,
    },
    UserRole.API_CLIENT: {
        Permission.PREDICT_READ,
        Permission.PREDICT_WRITE,
        Permission.MODEL_READ,
        Permission.DATA_READ,
    },
}


class User(BaseModel):
    """User model for authentication and authorization."""

    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    permissions: Set[Permission] = set()

    def __init__(self, **data):
        super().__init__(**data)
        # Set permissions based on role
        self.permissions = ROLE_PERMISSIONS.get(self.role, set())

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(perm in self.permissions for perm in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(perm in self.permissions for perm in permissions)


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # Subject (user ID)
    username: str
    role: UserRole
    exp: datetime
    iat: datetime
    jti: str  # JWT ID

    @validator("exp", "iat", pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
        return v


class AuthenticationService:
    """Handles authentication operations."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.algorithm = "HS256"

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_access_token(self, user: User) -> str:
        """Create JWT access token."""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.settings.api.access_token_expire_minutes)

        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "exp": expire,
            "iat": now,
            "jti": secrets.token_urlsafe(32),
        }

        token = jwt.encode(
            payload, self.settings.api.secret_key, algorithm=self.algorithm
        )

        self.logger.info(
            "Access token created",
            user_id=user.id,
            username=user.username,
            expires_at=expire.isoformat(),
        )

        return token

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, self.settings.api.secret_key, algorithms=[self.algorithm]
            )

            token_payload = TokenPayload(**payload)

            # Check if token is expired
            if token_payload.exp < datetime.utcnow():
                raise UnauthorizedError("Token has expired")

            return token_payload

        except jwt.InvalidTokenError as e:
            self.logger.warning("Invalid token provided", error=str(e))
            raise UnauthorizedError("Invalid token")
        except Exception as e:
            self.logger.error("Token verification failed", error=str(e))
            raise UnauthorizedError("Token verification failed")

    def create_api_key(self, user_id: str, name: str) -> str:
        """Create API key for programmatic access."""
        # Create a unique API key
        key_data = f"{user_id}:{name}:{secrets.token_urlsafe(32)}"
        api_key = hashlib.sha256(key_data.encode()).hexdigest()

        self.logger.info(
            "API key created", user_id=user_id, key_name=name, key_prefix=api_key[:8]
        )

        return api_key


class AuthorizationService:
    """Handles authorization operations."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def check_permission(self, user: User, required_permission: Permission) -> None:
        """Check if user has required permission."""
        if not user.is_active:
            raise ForbiddenError("User account is inactive")

        if not user.has_permission(required_permission):
            self.logger.warning(
                "Permission denied",
                user_id=user.id,
                username=user.username,
                required_permission=required_permission.value,
                user_permissions=[p.value for p in user.permissions],
            )
            raise ForbiddenError(f"Permission '{required_permission.value}' required")

    def check_any_permission(
        self, user: User, required_permissions: List[Permission]
    ) -> None:
        """Check if user has any of the required permissions."""
        if not user.is_active:
            raise ForbiddenError("User account is inactive")

        if not user.has_any_permission(required_permissions):
            self.logger.warning(
                "Permission denied - no matching permissions",
                user_id=user.id,
                username=user.username,
                required_permissions=[p.value for p in required_permissions],
                user_permissions=[p.value for p in user.permissions],
            )
            raise ForbiddenError("Insufficient permissions")

    def check_resource_access(
        self, user: User, resource_owner_id: str, required_permission: Permission
    ) -> None:
        """Check if user can access a specific resource."""
        # Admin can access everything
        if user.role == UserRole.ADMIN:
            return

        # Users can access their own resources
        if user.id == resource_owner_id:
            self.check_permission(user, required_permission)
            return

        # Otherwise, need admin permission
        raise ForbiddenError("Access denied to resource")


class RateLimiter:
    """Rate limiting implementation."""

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
        self.limits = {
            "default": (100, 3600),  # 100 requests per hour
            "auth": (10, 300),  # 10 auth attempts per 5 minutes
            "predict": (1000, 3600),  # 1000 predictions per hour
        }

    def is_allowed(self, identifier: str, limit_type: str = "default") -> bool:
        """Check if request is allowed under rate limit."""
        now = datetime.utcnow()
        limit, window = self.limits.get(limit_type, self.limits["default"])

        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time
                for req_time in self.requests[identifier]
                if (now - req_time).total_seconds() < window
            ]
        else:
            self.requests[identifier] = []

        # Check limit
        if len(self.requests[identifier]) >= limit:
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True

    def get_reset_time(
        self, identifier: str, limit_type: str = "default"
    ) -> Optional[datetime]:
        """Get when rate limit resets for identifier."""
        if identifier not in self.requests or not self.requests[identifier]:
            return None

        _, window = self.limits.get(limit_type, self.limits["default"])
        oldest_request = min(self.requests[identifier])
        return oldest_request + timedelta(seconds=window)


class SecurityHeaders:
    """Security headers for HTTP responses."""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }


class InputValidator:
    """Input validation and sanitization."""

    @staticmethod
    def validate_username(username: str) -> str:
        """Validate and sanitize username."""
        if not username or len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long")

        if len(username) > 50:
            raise ValidationError("Username must be less than 50 characters")

        # Allow only alphanumeric and underscore
        if not username.replace("_", "").isalnum():
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores"
            )

        return username.lower().strip()

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format."""
        import re

        email = email.strip().lower()

        if not email:
            raise ValidationError("Email is required")

        # Basic email validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")

        return email

    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password strength."""
        if not password:
            raise ValidationError("Password is required")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")

        if len(password) > 128:
            raise ValidationError("Password must be less than 128 characters")

        # Check for at least one uppercase, lowercase, digit, and special character
        import re

        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "Password must contain at least one special character"
            )

        return password


# Global service instances
auth_service = AuthenticationService()
authz_service = AuthorizationService()
rate_limiter = RateLimiter()
input_validator = InputValidator()


def require_permission(permission: Permission):
    """Decorator to require specific permission."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented with dependency injection in FastAPI
            # For now, it's a placeholder for the concept
            user = kwargs.get("current_user")
            if user:
                authz_service.check_permission(user, permission)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if user:
                authz_service.check_any_permission(user, permissions)
            return func(*args, **kwargs)

        return wrapper

    return decorator
