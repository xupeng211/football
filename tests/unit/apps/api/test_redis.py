from unittest.mock import AsyncMock, patch

# The module to be tested
import apps.api.redis
import pytest
from redis.asyncio.exceptions import ConnectionError as AsyncConnectionError

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


class TestCheckRedisConnectionAsync:
    """Tests for the check_redis_connection_async function."""

    async def test_check_skipped_in_test_env(self, monkeypatch):
        """Test that the check is skipped when in a test environment."""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
        is_ok, message = await apps.api.redis.check_redis_connection_async()
        assert is_ok is True
        assert "Redis check skipped" in message

    async def test_client_not_configured(self, monkeypatch):
        """Test failure when the async_redis_client is not configured."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        with patch("apps.api.redis.async_redis_client", None):
            is_ok, message = await apps.api.redis.check_redis_connection_async()
            assert is_ok is False
            assert "Redis client not configured" in message

    async def test_connection_successful(self, monkeypatch):
        """Test success when the redis client can ping successfully."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        with patch("apps.api.redis.async_redis_client", mock_client):
            is_ok, message = await apps.api.redis.check_redis_connection_async()
            assert is_ok is True
            assert message == "Redis connection successful."
            mock_client.ping.assert_awaited_once()

    async def test_ping_returns_false(self, monkeypatch):
        """Test failure when the redis client ping returns False."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_client = AsyncMock()
        mock_client.ping.return_value = False
        with patch("apps.api.redis.async_redis_client", mock_client):
            is_ok, message = await apps.api.redis.check_redis_connection_async()
            assert is_ok is False
            assert "PING returned False" in message
            mock_client.ping.assert_awaited_once()

    async def test_connection_error_on_ping(self, monkeypatch):
        """Test failure when pinging raises a ConnectionError."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_client = AsyncMock()
        mock_client.ping.side_effect = AsyncConnectionError("Cannot connect")
        with patch("apps.api.redis.async_redis_client", mock_client):
            is_ok, message = await apps.api.redis.check_redis_connection_async()
            assert is_ok is False
            assert "Redis connection failed: Cannot connect" in message
            mock_client.ping.assert_awaited_once()


class TestGetRedisClient:
    """Tests for the get_redis_client dependency."""

    async def test_get_client_success(self):
        """Test that the dependency yields the configured client."""
        mock_client = AsyncMock()
        with patch("apps.api.redis.async_redis_client", mock_client):
            async for client in apps.api.redis.get_redis_client():
                assert client is mock_client

    async def test_get_client_not_configured(self):
        """Test that the dependency raises an error if the client is not configured."""
        with patch("apps.api.redis.async_redis_client", None):
            with pytest.raises(ConnectionError, match="Redis client not configured"):
                async for _ in apps.api.redis.get_redis_client():
                    pass  # This should not be reached
