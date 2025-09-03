"""
Rate limiting functionality for API security.

Provides configurable rate limiting to prevent abuse and ensure fair usage.
"""

import time
from collections import defaultdict

from .models import SecurityConfig


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""

    def __init__(self, config: SecurityConfig) -> None:
        """Initialize rate limiter with configuration."""
        self.config = config
        self.requests: dict[str, list] = defaultdict(list)

    def is_allowed(
        self, identifier: str, window_seconds: int = 60, max_requests: int = 100
    ) -> bool:
        """
        Check if request is allowed based on rate limits.

        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            window_seconds: Time window in seconds
            max_requests: Maximum requests allowed in window

        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()

        # Clean old requests outside the window
        self.requests[identifier] = [
            req_time
            for req_time in self.requests[identifier]
            if current_time - req_time < window_seconds
        ]

        # Check if limit exceeded
        if len(self.requests[identifier]) >= max_requests:
            return False

        # Add current request
        self.requests[identifier].append(current_time)
        return True

    def get_remaining_requests(
        self, identifier: str, window_seconds: int = 60, max_requests: int = 100
    ) -> int:
        """Get number of remaining requests for identifier."""
        current_time = time.time()

        # Clean old requests
        self.requests[identifier] = [
            req_time
            for req_time in self.requests[identifier]
            if current_time - req_time < window_seconds
        ]

        return max(0, max_requests - len(self.requests[identifier]))

    def reset_limit(self, identifier: str) -> None:
        """Reset rate limit for identifier."""
        if identifier in self.requests:
            del self.requests[identifier]
