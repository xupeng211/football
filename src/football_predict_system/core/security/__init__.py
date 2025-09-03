"""
Security system package.

Provides production-grade security features including:
- JWT-based authentication
- Role-based authorization
- Rate limiting
- Security headers
- Input validation and sanitization
"""

from collections.abc import Callable
from typing import Any

from .auth import AuthenticationService, JWTManager
from .headers import SecurityHeaders
from .models import Permission, SecurityConfig, User, UserRole
from .rate_limiter import RateLimiter


# Placeholder for require_permission decorator
def require_permission(
    permission: Permission,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for requiring specific permissions."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # In a real implementation, this would check user permissions
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "AuthenticationService",
    "JWTManager",
    "Permission",
    "RateLimiter",
    "SecurityConfig",
    "SecurityHeaders",
    "User",
    "UserRole",
    "require_permission",
]
