# tests/unit/apps/api/test_redis.py

import importlib
from unittest.mock import MagicMock, patch

from redis.exceptions import ConnectionError, RedisError

# The module to be tested
import apps.api.redis


class TestRedisClientInitialization:
    """Tests for the module-level Redis client initialization."""

    @patch("redis.from_url")
    @patch("os.getenv", return_value="redis://fake-redis-url")
    def test_client_created_when_url_is_set(self, mock_getenv, mock_from_url):
        """Test that the redis_client is created when REDIS_URL is set."""
        importlib.reload(apps.api.redis)
        mock_from_url.assert_called_once_with("redis://fake-redis-url")
        assert apps.api.redis.redis_client is not None

    @patch("os.getenv", return_value=None)
    def test_client_is_none_when_url_is_not_set(self, mock_getenv):
        """Test that redis_client is None when REDIS_URL is not set."""
        importlib.reload(apps.api.redis)
        assert apps.api.redis.redis_client is None

    @patch("redis.from_url", side_effect=RedisError("Connection failed"))
    def test_client_is_none_on_redis_error(self, mock_from_url, monkeypatch):
        """Test that redis_client is None if creation raises RedisError."""
        monkeypatch.setenv("REDIS_URL", "redis://bad-redis-url")
        importlib.reload(apps.api.redis)
        assert apps.api.redis.redis_client is None


class TestCheckRedisConnection:
    """Tests for the check_redis_connection function."""

    def test_check_skipped_in_test_env(self, monkeypatch):
        """Test that the check is skipped when in a test environment."""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
        is_ok, message = apps.api.redis.check_redis_connection()
        assert is_ok is True
        assert "Redis check skipped" in message

    def test_client_not_configured(self, monkeypatch):
        """Test failure when the redis_client is not configured."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        with patch("apps.api.redis.redis_client", None):
            is_ok, message = apps.api.redis.check_redis_connection()
            assert is_ok is False
            assert "Redis client not configured" in message

    def test_connection_successful(self, monkeypatch):
        """Test success when the redis client can ping successfully."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        with patch("apps.api.redis.redis_client", mock_client):
            is_ok, message = apps.api.redis.check_redis_connection()
            assert is_ok is True
            assert message == "Redis connection successful."

    def test_ping_returns_false(self, monkeypatch):
        """Test failure when the redis client ping returns False."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_client = MagicMock()
        mock_client.ping.return_value = False
        with patch("apps.api.redis.redis_client", mock_client):
            is_ok, message = apps.api.redis.check_redis_connection()
            assert is_ok is False
            assert "PING returned False" in message

    def test_connection_error_on_ping(self, monkeypatch):
        """Test failure when pinging raises a ConnectionError."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_client = MagicMock()
        mock_client.ping.side_effect = ConnectionError("Cannot connect")
        with patch("apps.api.redis.redis_client", mock_client):
            is_ok, message = apps.api.redis.check_redis_connection()
            assert is_ok is False
            assert "Redis connection failed: Cannot connect" in message
