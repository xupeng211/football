# tests/unit/data_pipeline/sources/test_football_api.py

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from data_pipeline.sources.football_api import FootballAPICollector


@pytest.mark.asyncio
class TestFootballAPICollector:
    """Tests for the FootballAPICollector."""

    @patch("data_pipeline.sources.football_api.settings")
    def test_init_with_api_key_from_settings(self, mock_settings):
        """Test that the API key is taken from settings if not provided."""
        mock_settings.football_api_key = "key_from_settings"
        collector = FootballAPICollector()
        assert collector.api_key == "key_from_settings"

    def test_init_with_explicit_api_key(self):
        """Test that an explicitly provided API key is used."""
        collector = FootballAPICollector(api_key="explicit_key")
        assert collector.api_key == "explicit_key"

    @patch("httpx.AsyncClient")
    async def test_context_manager_with_api_key(self, mock_async_client_class):
        """Test the async context manager sets up and tears down the session with an API key."""
        mock_session = AsyncMock()
        mock_async_client_class.return_value = mock_session

        collector = FootballAPICollector(api_key="test_key")
        async with collector as instance:
            assert instance is collector
            mock_async_client_class.assert_called_once()
            # Check that the auth token is in the headers
            assert "X-Auth-Token" in mock_async_client_class.call_args.kwargs["headers"]
            assert (
                mock_async_client_class.call_args.kwargs["headers"]["X-Auth-Token"]
                == "test_key"
            )

        # Check that the session is closed on exit
        mock_session.aclose.assert_awaited_once()

    async def test_collect_matches_raises_error_if_no_session(self):
        """Test that a RuntimeError is raised if the session is not active."""
        collector = FootballAPICollector()
        with pytest.raises(RuntimeError, match="需要在async with语句中使用"):
            await collector.collect_matches_by_date(date(2024, 1, 1), date(2024, 1, 2))

    async def test_collect_team_info_raises_error_if_no_session(self):
        """Test that a RuntimeError is raised if the session is not active."""
        collector = FootballAPICollector()
        with pytest.raises(RuntimeError, match="需要在async with语句中使用"):
            await collector.collect_team_info(["1", "2"])

    @patch(
        "data_pipeline.sources.football_api.FootballAPICollector._generate_mock_matches"
    )
    async def test_collect_matches_exception_handling(self, mock_generate):
        """Test that exceptions during match collection are caught and raised."""
        mock_generate.side_effect = Exception("API fetch failed")
        collector = FootballAPICollector()
        async with collector:
            with pytest.raises(Exception, match="API fetch failed"):
                await collector.collect_matches_by_date(
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 2),
                    leagues=["PL"],
                )
