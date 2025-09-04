"""
Simplified data collection tests focused on coverage improvement.

Tests the core functionality of data collection tasks.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from football_predict_system.data_platform.flows.data_collection import (
    collect_matches_task,
    collect_teams_task,
    store_matches_task,
    store_teams_task,
)


class TestCollectionTasks:
    """Test collection tasks."""

    @pytest.mark.asyncio
    async def test_collect_matches_basic(self):
        """Test basic match collection."""

        mock_collector = AsyncMock()
        mock_stats = MagicMock()
        mock_stats.records_fetched = 2
        mock_stats.model_dump.return_value = {"records_fetched": 2}

        df = pd.DataFrame({"id": [1, 2], "team": ["A", "B"]})
        mock_collector.collect.return_value = (df, mock_stats)
        mock_collector.close = AsyncMock()

        module_path = "football_predict_system.data_platform.flows.data_collection"
        with patch(f"{module_path}.FootballDataAPICollector") as mock_class:
            mock_class.return_value = mock_collector

            result = await collect_matches_task.fn(competition_id=1)

        assert result["competition_id"] == 1
        assert len(result["data"]) == 2
        mock_collector.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_teams_basic(self):
        """Test basic team collection."""

        mock_collector = AsyncMock()
        df = pd.DataFrame({"id": [1], "name": ["Team A"]})
        mock_collector.fetch_teams.return_value = df
        mock_collector.close = AsyncMock()

        module_path = "football_predict_system.data_platform.flows.data_collection"
        with patch(f"{module_path}.FootballDataAPICollector") as mock_class:
            mock_class.return_value = mock_collector

            result = await collect_teams_task.fn(competition_id=1)

        assert result["competition_id"] == 1
        assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_store_matches_basic(self) -> None:
        """Test basic match storage."""

        data = {"data": [{"id": 1, "team": "A"}], "competition_id": 1}

        mock_writer = AsyncMock()
        mock_writer.upsert_matches.return_value = {
            "inserted": 1,
            "updated": 0,
            "failed": 0,
        }

        module_path = "football_predict_system.data_platform.flows.data_collection"
        with patch(f"{module_path}.DatabaseWriter") as mock_class:
            mock_class.return_value = mock_writer

            result = await store_matches_task.fn(data)

        assert result["inserted"] == 1

    @pytest.mark.asyncio
    async def test_store_teams_basic(self):
        """Test basic team storage."""

        data = {"data": [{"id": 1, "name": "Team A"}], "competition_id": 1}

        mock_writer = AsyncMock()
        mock_writer.upsert_teams.return_value = {
            "inserted": 1,
            "updated": 0,
            "failed": 0,
        }

        module_path = "football_predict_system.data_platform.flows.data_collection"
        with patch(f"{module_path}.DatabaseWriter") as mock_class:
            mock_class.return_value = mock_writer

            result = await store_teams_task.fn(data)

        assert result["inserted"] == 1

    @pytest.mark.asyncio
    async def test_empty_data_handling(self):
        """Test handling of empty data."""

        empty_data = {"data": [], "competition_id": 1}

        # Store matches with empty data
        result = await store_matches_task.fn(empty_data)
        assert result["inserted"] == 0

        # Store teams with empty data
        result = await store_teams_task.fn(empty_data)
        assert result["inserted"] == 0

    def test_task_attributes(self):
        """Test task attributes and configuration."""

        # Test task names
        assert collect_matches_task.name == "collect-matches"
        assert collect_teams_task.name == "collect-teams"
        assert store_matches_task.name == "store-matches"
        assert store_teams_task.name == "store-teams"

        # Test retry configurations
        assert collect_matches_task.retries == 3
        assert collect_teams_task.retries == 2
        assert store_matches_task.retries == 2
        assert store_teams_task.retries == 2

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test exception handling in tasks."""

        mock_collector = AsyncMock()
        mock_collector.collect.side_effect = RuntimeError("API Error")
        mock_collector.close = AsyncMock()

        module_path = "football_predict_system.data_platform.flows.data_collection"
        with patch(f"{module_path}.FootballDataAPICollector") as mock_class:
            mock_class.return_value = mock_collector

            with pytest.raises(RuntimeError):
                await collect_matches_task.fn(competition_id=1)

            # Ensure cleanup happens
            mock_collector.close.assert_called_once()


class TestFlowImports:
    """Test flow imports and structure."""

    def test_flow_imports(self):
        """Test that flow components can be imported."""

        from football_predict_system.data_platform.flows.data_collection import (
            daily_data_collection_flow,
        )

        # Basic attribute tests
        assert hasattr(daily_data_collection_flow, "fn")
        assert callable(daily_data_collection_flow.fn)

    def test_task_callable_functions(self):
        """Test that task functions are callable."""

        assert callable(collect_matches_task.fn)
        assert callable(collect_teams_task.fn)
        assert callable(store_matches_task.fn)
        assert callable(store_teams_task.fn)
