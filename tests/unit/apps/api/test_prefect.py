# tests/unit/apps/api/test_prefect.py

from unittest.mock import AsyncMock, patch

import pytest
from football_predict_system.api.prefect import check_prefect_connection, check_prefect_connection_async
from prefect.exceptions import PrefectException


@pytest.mark.asyncio
class TestCheckPrefectConnectionAsync:
    """Tests for the check_prefect_connection_async function."""

    @patch("apps.api.prefect.get_client")
    @patch("apps.api.prefect.PREFECT_API_URL", "http://fake-prefect-url")
    async def test_connection_successful(self, mock_get_client):
        """Test when the Prefect API is healthy and reachable."""
        mock_client = AsyncMock()
        mock_client.api_healthcheck.return_value = True
        mock_get_client.return_value.__aenter__.return_value = mock_client

        is_ok, message = await check_prefect_connection_async()

        assert is_ok is True
        assert message == "Prefect API connection successful."

    @patch("apps.api.prefect.get_client")
    @patch("apps.api.prefect.PREFECT_API_URL", "http://fake-prefect-url")
    async def test_connection_unhealthy(self, mock_get_client):
        """Test when the Prefect API is reachable but not healthy."""
        mock_client = AsyncMock()
        mock_client.api_healthcheck.return_value = False
        mock_get_client.return_value.__aenter__.return_value = mock_client

        is_ok, message = await check_prefect_connection_async()

        assert is_ok is False
        assert message == "Prefect API is not healthy."

    @patch("apps.api.prefect.get_client")
    @patch("apps.api.prefect.PREFECT_API_URL", "http://fake-prefect-url")
    async def test_prefect_exception(self, mock_get_client):
        """Test when a PrefectException is raised."""
        mock_get_client.side_effect = PrefectException("Auth error")

        is_ok, message = await check_prefect_connection_async()

        assert is_ok is False
        assert "Prefect API connection failed: Auth error" in message

    @patch("apps.api.prefect.get_client")
    @patch("apps.api.prefect.PREFECT_API_URL", "http://fake-prefect-url")
    async def test_unexpected_exception(self, mock_get_client):
        """Test when an unexpected exception occurs."""
        mock_get_client.side_effect = Exception("Something broke")

        is_ok, message = await check_prefect_connection_async()

        assert is_ok is False
        assert "An unexpected error occurred: Something broke" in message

    @patch("apps.api.prefect.PREFECT_API_URL", None)
    async def test_no_api_url(self):
        """Test when PREFECT_API_URL is not configured."""
        is_ok, message = await check_prefect_connection_async()
        assert is_ok is False
        assert "PREFECT_API_URL not set" in message


class TestCheckPrefectConnectionSync:
    """Tests for the sync wrapper check_prefect_connection."""

    def test_skipped_in_test_env(self, monkeypatch):
        """Test that the check is skipped in a test environment."""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
        is_ok, message = check_prefect_connection()
        assert is_ok is True
        assert "Prefect check skipped" in message

    @patch("apps.api.prefect.check_prefect_connection_async")
    def test_sync_wrapper_calls_async_success(self, mock_async_check, monkeypatch):
        """Test that the sync wrapper correctly calls the async function."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_async_check.return_value = (True, "Success")

        is_ok, message = check_prefect_connection()

        assert is_ok is True
        assert message == "Success"
        mock_async_check.assert_called_once()

    @patch("apps.api.prefect.asyncio.run")
    def test_sync_wrapper_handles_exception(self, mock_asyncio_run, monkeypatch):
        """Test that the sync wrapper handles exceptions from asyncio.run."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_asyncio_run.side_effect = Exception("Async run failed")

        is_ok, message = check_prefect_connection()

        assert is_ok is False
        assert "Failed to run async check: Async run failed" in message
