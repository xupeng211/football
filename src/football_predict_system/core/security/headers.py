"""
Security headers management for HTTP responses.

Provides secure header configuration for API responses.
"""


class SecurityHeaders:
    """Security headers configuration for HTTP responses."""

    @staticmethod
    def get_security_headers() -> dict[str, str]:
        """Get security headers dictionary."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }

    @staticmethod
    def apply_headers(response_headers: dict[str, str]) -> dict[str, str]:
        """Apply security headers to response."""
        security_headers = SecurityHeaders.get_security_headers()
        response_headers.update(security_headers)
        return response_headers
