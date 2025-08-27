"""
Tests for the Football API Collector.
"""

from datetime import date

import pytest

from data_pipeline.sources.football_api import FootballAPICollector, Match, Team


@pytest.mark.asyncio
async def test_collect_matches_by_date_success():
    """Test successful collection of matches by date."""
    async with FootballAPICollector(api_key="test_key") as collector:
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)
        leagues = ["PL"]
        matches = await collector.collect_matches_by_date(start, end, leagues)
        assert isinstance(matches, list)
        if matches:
            assert isinstance(matches[0], Match)
        # The mock function generates a specific number of matches
        assert len(matches) > 0


@pytest.mark.asyncio
async def test_collect_team_info_success():
    """Test successful collection of team info."""
    async with FootballAPICollector(api_key="test_key") as collector:
        team_ids = ["1", "2", "3"]
        teams = await collector.collect_team_info(team_ids)
        assert isinstance(teams, list)
        assert len(teams) == 3
        if teams:
            assert isinstance(teams[0], Team)
            assert teams[0].team_id == "1"


@pytest.mark.asyncio
async def test_collector_without_context_manager():
    """Test that collector raises RuntimeError when not used with a context manager."""
    collector = FootballAPICollector(api_key="test_key")
    start = date(2024, 1, 1)
    end = date(2024, 1, 3)
    with pytest.raises(RuntimeError, match="需要在async with语句中使用"):
        await collector.collect_matches_by_date(start, end)

    with pytest.raises(RuntimeError, match="需要在async with语句中使用"):
        await collector.collect_team_info(["1"])


@pytest.mark.asyncio
async def test_context_manager_session_handling():
    """Test that the session is created and closed correctly."""
    collector = FootballAPICollector(api_key="test_key")
    assert collector.session is None
    async with collector:
        assert collector.session is not None
        assert not collector.session.is_closed
    assert collector.session.is_closed
