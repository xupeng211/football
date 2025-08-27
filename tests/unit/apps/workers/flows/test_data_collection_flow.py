"""
Unit tests for the data collection flow.
"""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from prefect.testing.utilities import prefect_test_harness

from apps.workers.flows.data_collection_flow import (
    collect_matches_task,
    collect_odds_task,
    daily_data_collection_flow,
    historical_data_backfill_flow,
    store_data_task,
    validate_and_clean_data,
)


@pytest.fixture(autouse=True)
def prefect_test_fixture():
    """Enable Prefect test harness for all tests in this module."""
    with prefect_test_harness():
        yield


class TestCollectionTasks:
    """Tests for individual Prefect tasks."""

    @pytest.mark.asyncio
    async def test_collect_matches_task(self):
        """Tests the match collection task."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 1)
        leagues = ["PL"]

        # The task currently returns placeholder data
        result = await collect_matches_task.fn(start_date, end_date, leagues)

        assert isinstance(result, list)
        assert len(result) == 5  # Placeholder generates 5 matches
        assert "match_id" in result[0]
        assert result[0]["league"] == "PL"

    @pytest.mark.asyncio
    async def test_collect_odds_task(self):
        """Tests the odds collection task."""
        match_ids = ["match_1", "match_2"]

        # The task currently returns placeholder data
        result = await collect_odds_task.fn(match_ids)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["match_id"] == "match_1"
        assert "home_odds" in result[0]

    def test_validate_and_clean_data(self):
        """Tests the data validation and cleaning task."""
        matches = [{"id": 1}]
        odds = [{"match_id": 1}]

        # The task returns placeholder stats
        result = validate_and_clean_data.fn(matches, odds)

        assert isinstance(result, dict)
        assert result["original_matches"] == 1
        assert result["cleaned_matches"] == 1
        assert "quality_score" in result

    @pytest.mark.asyncio
    async def test_store_data_task(self):
        """Tests the data storage task."""
        matches = [{"id": 1}]
        odds = [{"match_id": 1}]

        result = await store_data_task.fn(matches, odds)

        assert isinstance(result, dict)
        assert result["stored_matches"] == 1
        assert result["success"] is True


class TestCollectionFlows:
    """Tests for the Prefect flows."""

    @patch(
        "apps.workers.flows.data_collection_flow.store_data_task",
        new_callable=AsyncMock,
    )
    @patch("apps.workers.flows.data_collection_flow.validate_and_clean_data")
    @patch(
        "apps.workers.flows.data_collection_flow.collect_odds_task",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.workers.flows.data_collection_flow.collect_matches_task",
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_daily_data_collection_flow(
        self, mock_matches, mock_odds, mock_validate, mock_store
    ):
        """Tests the daily data collection flow's orchestration logic."""
        target_date = date(2023, 5, 10)
        mock_matches.return_value = [{"match_id": "m1"}]
        mock_odds.return_value = [{"odds_id": "o1"}]
        mock_validate.return_value = {"status": "validated"}
        mock_store.return_value = {"status": "stored"}

        result = await daily_data_collection_flow.fn(target_date=target_date)

        mock_matches.assert_called_once_with(
            target_date, target_date, ["PL", "BL1", "SA", "PD", "FL1"]
        )
        mock_odds.assert_called_once_with(["m1"])
        mock_validate.assert_called_once()
        mock_store.assert_called_once()
        assert result["success"] is True
        assert result["matches_collected"] == 1
        assert result["storage_stats"]["status"] == "stored"

    @patch(
        "apps.workers.flows.data_collection_flow.store_data_task",
        new_callable=AsyncMock,
    )
    @patch("apps.workers.flows.data_collection_flow.validate_and_clean_data")
    @patch(
        "apps.workers.flows.data_collection_flow.collect_odds_task",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.workers.flows.data_collection_flow.collect_matches_task",
        new_callable=AsyncMock,
    )
    @pytest.mark.asyncio
    async def test_historical_data_backfill_flow(
        self, mock_matches, mock_odds, mock_validate, mock_store
    ):
        """Tests the historical data backfill flow's logic."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 10)  # 10 days, should result in two loops
        mock_matches.return_value = [{"match_id": "m1"}]
        mock_odds.return_value = [{"odds_id": "o1"}]

        await historical_data_backfill_flow.fn(start_date=start_date, end_date=end_date)

        assert mock_matches.call_count == 2
        assert mock_odds.call_count == 2
        assert mock_matches.call_args_list[0].args[0] == date(2023, 1, 1)
        assert mock_matches.call_args_list[0].args[1] == date(2023, 1, 7)
        assert mock_matches.call_args_list[1].args[0] == date(2023, 1, 8)
        assert mock_matches.call_args_list[1].args[1] == date(2023, 1, 10)
