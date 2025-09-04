"""
Tests for rate limiter functionality.

Complete coverage tests for RateLimiter class and rate limiting logic.
"""

from unittest.mock import patch

from football_predict_system.core.security.models import SecurityConfig
from football_predict_system.core.security.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        assert limiter.config is config
        assert isinstance(limiter.requests, dict)
        assert len(limiter.requests) == 0

    def test_rate_limiter_requests_is_defaultdict(self):
        """Test requests attribute is defaultdict."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Accessing non-existent key should return empty list
        assert limiter.requests["non-existent"] == []
        assert isinstance(limiter.requests["non-existent"], list)

    @patch("time.time")
    def test_is_allowed_first_request(self, mock_time):
        """Test first request is always allowed."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        result = limiter.is_allowed("user1")

        assert result is True
        assert len(limiter.requests["user1"]) == 1
        assert limiter.requests["user1"][0] == 1000.0

    @patch("time.time")
    def test_is_allowed_multiple_requests_within_limit(self, mock_time):
        """Test multiple requests within limit are allowed."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Allow 5 requests
        for i in range(5):
            mock_time.return_value = 1000.0 + i
            result = limiter.is_allowed("user1", max_requests=10)
            assert result is True

        assert len(limiter.requests["user1"]) == 5

    @patch("time.time")
    def test_is_allowed_exceeds_limit(self, mock_time):
        """Test requests exceeding limit are rejected."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Fill up to limit (3 requests)
        for i in range(3):
            mock_time.return_value = 1000.0 + i
            result = limiter.is_allowed("user1", max_requests=3)
            assert result is True

        # Next request should be rejected
        mock_time.return_value = 1003.0
        result = limiter.is_allowed("user1", max_requests=3)
        assert result is False

        # Should still have 3 requests in memory
        assert len(limiter.requests["user1"]) == 3

    @patch("time.time")
    def test_is_allowed_window_cleanup(self, mock_time):
        """Test old requests are cleaned up outside window."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Add requests at time 1000
        mock_time.return_value = 1000.0
        for _i in range(3):
            limiter.is_allowed("user1", window_seconds=60, max_requests=3)
            mock_time.return_value += 1

        # Move time forward beyond window (60 seconds)
        mock_time.return_value = 1065.0  # 65 seconds later

        # This request should be allowed as old ones are cleaned up
        result = limiter.is_allowed("user1", window_seconds=60, max_requests=3)
        assert result is True

        # Should only have 1 request (the current one)
        assert len(limiter.requests["user1"]) == 1

    @patch("time.time")
    def test_is_allowed_partial_window_cleanup(self, mock_time):
        """Test partial cleanup of requests in window."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Add requests at different times
        mock_time.return_value = 1000.0
        limiter.is_allowed("user1", window_seconds=60, max_requests=5)

        mock_time.return_value = 1010.0
        limiter.is_allowed("user1", window_seconds=60, max_requests=5)

        mock_time.return_value = 1070.0  # 70 seconds from start
        limiter.is_allowed("user1", window_seconds=60, max_requests=5)

        # Should have cleaned up 1000.0, kept 1010.0, added 1070.0
        # But 1010.0 is also cleaned up because 1070 - 60 = 1010, so 1010 is at boundary
        assert len(limiter.requests["user1"]) == 1

    @patch("time.time")
    def test_is_allowed_different_identifiers(self, mock_time):
        """Test different identifiers are tracked separately."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Fill limit for user1
        for _i in range(3):
            result = limiter.is_allowed("user1", max_requests=3)
            assert result is True
            mock_time.return_value += 1

        # user1 should be blocked
        result = limiter.is_allowed("user1", max_requests=3)
        assert result is False

        # user2 should still be allowed
        result = limiter.is_allowed("user2", max_requests=3)
        assert result is True

    @patch("time.time")
    def test_get_remaining_requests_empty(self, mock_time):
        """Test get_remaining_requests with no prior requests."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        remaining = limiter.get_remaining_requests("user1", max_requests=10)
        assert remaining == 10

    @patch("time.time")
    def test_get_remaining_requests_with_usage(self, mock_time):
        """Test get_remaining_requests with some usage."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Use 3 requests
        for _i in range(3):
            limiter.is_allowed("user1", max_requests=10)
            mock_time.return_value += 1

        remaining = limiter.get_remaining_requests("user1", max_requests=10)
        assert remaining == 7

    @patch("time.time")
    def test_get_remaining_requests_at_limit(self, mock_time):
        """Test get_remaining_requests when at limit."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Use all requests
        for _i in range(5):
            limiter.is_allowed("user1", max_requests=5)

        remaining = limiter.get_remaining_requests("user1", max_requests=5)
        assert remaining == 0

    @patch("time.time")
    def test_get_remaining_requests_cleanup(self, mock_time):
        """Test get_remaining_requests cleans up old requests."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Add old requests
        mock_time.return_value = 1000.0
        for _i in range(3):
            limiter.is_allowed("user1", window_seconds=60, max_requests=5)

        # Move time forward
        mock_time.return_value = 1065.0

        # Check remaining - should clean up old requests
        remaining = limiter.get_remaining_requests(
            "user1", window_seconds=60, max_requests=5
        )
        assert remaining == 5  # All cleaned up

    def test_reset_limit_existing_identifier(self):
        """Test reset_limit removes existing identifier."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Add some requests
        with patch("time.time", return_value=1000.0):
            limiter.is_allowed("user1")
            limiter.is_allowed("user1")

        assert "user1" in limiter.requests
        assert len(limiter.requests["user1"]) == 2

        # Reset limit
        limiter.reset_limit("user1")

        assert "user1" not in limiter.requests

    def test_reset_limit_non_existent_identifier(self):
        """Test reset_limit with non-existent identifier doesn't error."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Should not raise error
        limiter.reset_limit("non-existent")

        # Should still be empty
        assert len(limiter.requests) == 0

    @patch("time.time")
    def test_rate_limiter_edge_case_zero_requests(self, mock_time):
        """Test rate limiter with zero max requests."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Should be rejected immediately
        result = limiter.is_allowed("user1", max_requests=0)
        assert result is False

    @patch("time.time")
    def test_rate_limiter_edge_case_one_request(self, mock_time):
        """Test rate limiter with max one request."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # First should be allowed
        result = limiter.is_allowed("user1", max_requests=1)
        assert result is True

        # Second should be rejected
        result = limiter.is_allowed("user1", max_requests=1)
        assert result is False

    @patch("time.time")
    def test_rate_limiter_window_edge_cases(self, mock_time):
        """Test rate limiter with different window sizes."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Very short window (1 second)
        mock_time.return_value = 1000.0
        limiter.is_allowed("user1", window_seconds=1, max_requests=2)

        mock_time.return_value = 1001.1  # Just over 1 second
        result = limiter.is_allowed("user1", window_seconds=1, max_requests=2)
        assert result is True  # Old request cleaned up

    @patch("time.time")
    def test_rate_limiter_concurrent_identifiers(self, mock_time):
        """Test rate limiter with multiple concurrent identifiers."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        identifiers = ["user1", "user2", "user3", "192.168.1.1"]

        # Each identifier should be independent
        for identifier in identifiers:
            for _i in range(3):
                result = limiter.is_allowed(identifier, max_requests=3)
                assert result is True
                mock_time.return_value += 0.1

        # All should be at limit
        for identifier in identifiers:
            result = limiter.is_allowed(identifier, max_requests=3)
            assert result is False

        assert len(limiter.requests) == 4

    @patch("time.time")
    def test_rate_limiter_time_precision(self, mock_time):
        """Test rate limiter handles time precision correctly."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Use precise timestamps
        mock_time.return_value = 1000.123456
        limiter.is_allowed("user1", window_seconds=60, max_requests=2)

        mock_time.return_value = 1000.654321
        result = limiter.is_allowed("user1", window_seconds=60, max_requests=2)
        assert result is True

        # Should be at limit
        result = limiter.is_allowed("user1", window_seconds=60, max_requests=2)
        assert result is False

    @patch("time.time")
    def test_get_remaining_requests_negative_protection(self, mock_time):
        """Test get_remaining_requests protects against negative values."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Manually add more requests than limit (edge case)
        limiter.requests["user1"] = [1000.0, 1001.0, 1002.0, 1003.0, 1004.0]

        # Should return 0, not negative
        remaining = limiter.get_remaining_requests("user1", max_requests=3)
        assert remaining == 0

    def test_rate_limiter_config_usage(self):
        """Test rate limiter uses provided config."""
        config = SecurityConfig(
            jwt_secret_key="test", requests_per_minute=120, burst_size=20
        )
        limiter = RateLimiter(config)

        assert limiter.config.requests_per_minute == 120
        assert limiter.config.burst_size == 20

    @patch("time.time")
    def test_rate_limiter_default_parameters(self, mock_time):
        """Test rate limiter default parameters work correctly."""
        mock_time.return_value = 1000.0

        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Should use default window_seconds=60, max_requests=100
        result = limiter.is_allowed("user1")
        assert result is True

        remaining = limiter.get_remaining_requests("user1")
        assert remaining == 99  # 100 - 1

    @patch("time.time")
    def test_rate_limiter_integration_scenario(self, mock_time):
        """Test comprehensive integration scenario."""
        config = SecurityConfig(jwt_secret_key="test")
        limiter = RateLimiter(config)

        # Simulate real usage pattern
        mock_time.return_value = 1000.0

        # User makes requests gradually
        for minute in range(3):
            for request in range(5):
                mock_time.return_value = 1000.0 + (minute * 60) + (request * 10)
                result = limiter.is_allowed(
                    "api_user", window_seconds=120, max_requests=10
                )

                if minute < 2:  # First 2 minutes should be fine
                    assert result is True
                # Third minute might hit limit

        # Check final state
        remaining = limiter.get_remaining_requests(
            "api_user", window_seconds=120, max_requests=10
        )
        assert remaining >= 0
