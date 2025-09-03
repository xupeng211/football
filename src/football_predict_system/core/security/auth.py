"""
Authentication and authorization services.

Handles JWT-based authentication and role-based authorization.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt

from ..config import get_settings
from ..exceptions import UnauthorizedError
from ..logging import get_logger
from .models import SecurityConfig, TokenPayload, UserRole

logger = get_logger(__name__)


class JWTManager:
    """Manages JWT token operations."""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.logger = get_logger(__name__)

    def create_access_token(self, user_id: str, role: UserRole) -> str:
        """Create JWT access token."""
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.config.jwt_expire_minutes)

        payload = {
            "user_id": user_id,
            "role": role.value,
            "exp": int(expires.timestamp()),
            "iat": int(now.timestamp()),
        }

        return jwt.encode(
            payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm
        )

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            return TokenPayload(
                user_id=payload["user_id"],
                role=UserRole(payload["role"]),
                exp=payload["exp"],
                iat=payload["iat"],
            )

        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expired")
            raise UnauthorizedError("Token expired")
        except jwt.InvalidTokenError as e:
            self.logger.warning("Invalid token provided", error=str(e))
            raise UnauthorizedError("Invalid token")
        except (ValueError, KeyError) as e:
            self.logger.error("Token verification failed", error=str(e))
            raise UnauthorizedError("Token verification failed")


class AuthenticationService:
    """Handles user authentication and authorization."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.jwt_manager = JWTManager(
            SecurityConfig(
                jwt_secret_key=self.settings.api.secret_key,
                jwt_algorithm="HS256",
                jwt_expire_minutes=self.settings.api.access_token_expire_minutes,
            )
        )

    def create_api_key(self, user_id: str, name: str) -> str:
        """Create API key for programmatic access."""
        # Create a unique API key
        key_data = f"{user_id}:{name}:{secrets.token_urlsafe(32)}"
        api_key = hashlib.sha256(key_data.encode()).hexdigest()

        self.logger.info("API key created", user_id=user_id, key_name=name)
        return api_key

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        """Authenticate user credentials."""
        # Placeholder implementation
        # In a real system, this would check against a user database
        if username == "admin" and password == "admin":  # nosec B105
            return {
                "user_id": "admin_user",
                "username": "admin",
                "role": UserRole.ADMIN,
            }
        return None

    def authorize_role(self, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role has required permissions."""
        role_hierarchy = {
            UserRole.GUEST: 0,
            UserRole.USER: 1,
            UserRole.API_CLIENT: 2,
            UserRole.ADMIN: 3,
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level
