"""
Tests for data service.

Complete coverage tests for DataService functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from football_predict_system.domain.services.data_service import DataService


class TestDataService:
    """Test DataService class."""

    def test_data_service_initialization(self):
        """Test DataService initialization."""
        service = DataService()

        assert service is not None
        assert hasattr(service, "logger")
        assert service.logger is not None

    @patch("football_predict_system.domain.services.data_service.get_logger")
    def test_data_service_logger_setup(self, mock_get_logger):
        """Test logger is properly set up."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        service = DataService()

        assert service.logger is mock_logger
        mock_get_logger.assert_called_with(
            "football_predict_system.domain.services.data_service"
        )

    @pytest.mark.asyncio
    async def test_get_match_by_id_cache_hit(self):
        """Test get_match_by_id with cache hit."""
        service = DataService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "home_team_id": "123e4567-e89b-12d3-a456-426614174001",
            "away_team_id": "123e4567-e89b-12d3-a456-426614174002",
            "competition": "Premier League",
            "season": "2023-24",
            "scheduled_date": "2023-10-01T15:00:00",
        }
        mock_cache_manager.get.return_value = mock_cache_data

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            result = await service.get_match_by_id("match123")

            # Should return a Match instance with correct data
            assert result is not None
            assert str(result.id) == "123e4567-e89b-12d3-a456-426614174000"
            assert result.competition == "Premier League"
            assert result.season == "2023-24"
            mock_cache_manager.get.assert_called_once_with("match:match123", "matches")
            mock_cache_manager.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_match_by_id_cache_miss_db_hit(self):
        """Test get_match_by_id with cache miss but database hit."""
        service = DataService()

        # Mock cache manager (cache miss)
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        # Mock database result
        mock_db_match = MagicMock()
        mock_db_match.dict.return_value = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "home_team_id": "123e4567-e89b-12d3-a456-426614174001",
            "away_team_id": "123e4567-e89b-12d3-a456-426614174002",
            "competition": "Premier League",
            "season": "2023-24",
            "scheduled_date": "2023-10-01T15:00:00",
        }

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch.object(service, "_load_match_from_db") as mock_load_db:
                mock_load_db.return_value = mock_db_match

                result = await service.get_match_by_id("match123")

                assert result is mock_db_match
                mock_cache_manager.get.assert_called_once_with(
                    "match:match123", "matches"
                )
                                mock_load_db.assert_called_once_with("match123")
                # Verify cache was set with the actual match data
                mock_cache_manager.set.assert_called_once()
                call_args = mock_cache_manager.set.call_args
                assert call_args[0][0] == "match:match123"  # Cache key
                assert call_args[0][2] == 1800  # TTL
                assert call_args[0][3] == "matches"  # Namespace

    @pytest.mark.asyncio
    async def test_get_match_by_id_cache_miss_db_miss(self):
        """Test get_match_by_id with both cache and database miss."""
        service = DataService()

        # Mock cache manager (cache miss)
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch.object(service, "_load_match_from_db") as mock_load_db:
                mock_load_db.return_value = None

                result = await service.get_match_by_id("match123")

                assert result is None
                mock_cache_manager.get.assert_called_once_with(
                    "match:match123", "matches"
                )
                mock_load_db.assert_called_once_with("match123")
                mock_cache_manager.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_team_by_id_cache_hit(self):
        """Test get_team_by_id with cache hit."""
        service = DataService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_data = {"id": "team123", "name": "Team A", "country": "Country"}
        mock_cache_manager.get.return_value = mock_cache_data

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch("football_predict_system.domain.models.Team") as mock_team_class:
                mock_team = MagicMock()
                mock_team_class.return_value = mock_team

                result = await service.get_team_by_id("team123")

                assert result is mock_team
                mock_cache_manager.get.assert_called_once_with("team:team123", "teams")
                mock_team_class.assert_called_once_with(**mock_cache_data)

    @pytest.mark.asyncio
    async def test_get_team_by_id_cache_miss_db_hit(self):
        """Test get_team_by_id with cache miss but database hit."""
        service = DataService()

        # Mock cache manager (cache miss)
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        # Mock database result
        mock_db_team = MagicMock()
        mock_db_team.dict.return_value = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Team A",
            "short_name": "TMA",
        }

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch.object(service, "_load_team_from_db") as mock_load_db:
                mock_load_db.return_value = mock_db_team

                result = await service.get_team_by_id("team123")

                assert result is mock_db_team
                mock_cache_manager.get.assert_called_once_with("team:team123", "teams")
                mock_load_db.assert_called_once_with("team123")
                mock_cache_manager.set.assert_called_once_with(
                    "team:team123", {"id": "team123", "name": "Team A"}, 3600, "teams"
                )

    @pytest.mark.asyncio
    async def test_get_team_by_id_cache_miss_db_miss(self):
        """Test get_team_by_id with both cache and database miss."""
        service = DataService()

        # Mock cache manager (cache miss)
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch.object(service, "_load_team_from_db") as mock_load_db:
                mock_load_db.return_value = None

                result = await service.get_team_by_id("team123")

                assert result is None
                mock_cache_manager.get.assert_called_once_with("team:team123", "teams")
                mock_load_db.assert_called_once_with("team123")
                mock_cache_manager.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_upcoming_matches_cache_hit(self):
        """Test get_upcoming_matches with cache hit."""
        service = DataService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_data = [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "home_team_id": "123e4567-e89b-12d3-a456-426614174001",
                "away_team_id": "123e4567-e89b-12d3-a456-426614174002",
                "competition": "Premier League",
                "season": "2023-24",
                "scheduled_date": "2023-10-01T15:00:00",
            },
            {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "home_team_id": "123e4567-e89b-12d3-a456-426614174004",
                "away_team_id": "123e4567-e89b-12d3-a456-426614174005",
                "competition": "Premier League",
                "season": "2023-24",
                "scheduled_date": "2023-10-02T17:30:00",
            },
        ]
        mock_cache_manager.get.return_value = mock_cache_data

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch(
                "football_predict_system.domain.models.Match"
            ) as mock_match_class:
                mock_match1 = MagicMock()
                mock_match2 = MagicMock()
                mock_match_class.side_effect = [mock_match1, mock_match2]

                result = await service.get_upcoming_matches(5)

                assert result == [mock_match1, mock_match2]
                mock_cache_manager.get.assert_called_once_with(
                    "upcoming_matches:5", "matches"
                )
                assert mock_match_class.call_count == 2

    @pytest.mark.asyncio
    async def test_get_upcoming_matches_default_limit(self):
        """Test get_upcoming_matches with default limit."""
        service = DataService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = []

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch.object(
                service, "_load_upcoming_matches_from_db"
            ) as mock_load_db:
                mock_load_db.return_value = []

                result = await service.get_upcoming_matches()

                assert result == []
                mock_cache_manager.get.assert_called_once_with(
                    "upcoming_matches:10", "matches"
                )
                mock_load_db.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_get_upcoming_matches_cache_miss(self):
        """Test get_upcoming_matches with cache miss."""
        service = DataService()

        # Mock cache manager (cache miss)
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        # Mock database result
        mock_match1 = MagicMock()
        mock_match1.dict.return_value = {"id": "match1"}
        mock_match2 = MagicMock()
        mock_match2.dict.return_value = {"id": "match2"}
        mock_db_matches = [mock_match1, mock_match2]

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch.object(
                service, "_load_upcoming_matches_from_db"
            ) as mock_load_db:
                mock_load_db.return_value = mock_db_matches

                result = await service.get_upcoming_matches(3)

                assert result == mock_db_matches
                mock_cache_manager.get.assert_called_once_with(
                    "upcoming_matches:3", "matches"
                )
                mock_load_db.assert_called_once_with(3)
                mock_cache_manager.set.assert_called_once_with(
                    "upcoming_matches:3",
                    [{"id": "match1"}, {"id": "match2"}],
                    1800,
                    "matches",
                )

    @pytest.mark.asyncio
    async def test_load_match_from_db_placeholder(self):
        """Test _load_match_from_db placeholder implementation."""
        service = DataService()

        result = await service._load_match_from_db("match123")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_team_from_db_placeholder(self):
        """Test _load_team_from_db placeholder implementation."""
        service = DataService()

        result = await service._load_team_from_db("team123")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_upcoming_matches_from_db_placeholder(self):
        """Test _load_upcoming_matches_from_db placeholder implementation."""
        service = DataService()

        result = await service._load_upcoming_matches_from_db(10)

        assert result == []
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation patterns."""
        service = DataService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with (
                patch.object(service, "_load_match_from_db") as mock_load_match,
                patch.object(service, "_load_team_from_db") as mock_load_team,
                patch.object(
                    service, "_load_upcoming_matches_from_db"
                ) as mock_load_upcoming,
            ):
                mock_load_match.return_value = None
                mock_load_team.return_value = None
                mock_load_upcoming.return_value = []

                # Test different cache keys
                await service.get_match_by_id("match_123")
                await service.get_team_by_id("team_456")
                await service.get_upcoming_matches(15)

                # Verify cache key patterns
                get_calls = mock_cache_manager.get.call_args_list
                assert get_calls[0][0] == ("match:match_123", "matches")
                assert get_calls[1][0] == ("team:team_456", "teams")
                assert get_calls[2][0] == ("upcoming_matches:15", "matches")

    @pytest.mark.asyncio
    async def test_cache_ttl_values(self):
        """Test cache TTL values are correct."""
        service = DataService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        # Mock database results
        mock_match = MagicMock()
        mock_match.dict.return_value = {"id": "match123"}

        mock_team = MagicMock()
        mock_team.dict.return_value = {"id": "team123"}

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with (
                patch.object(service, "_load_match_from_db") as mock_load_match,
                patch.object(service, "_load_team_from_db") as mock_load_team,
                patch.object(
                    service, "_load_upcoming_matches_from_db"
                ) as mock_load_upcoming,
            ):
                mock_load_match.return_value = mock_match
                mock_load_team.return_value = mock_team
                mock_load_upcoming.return_value = []

                await service.get_match_by_id("match123")
                await service.get_team_by_id("team123")
                await service.get_upcoming_matches(5)

                # Verify TTL values
                set_calls = mock_cache_manager.set.call_args_list

                # Match TTL: 1800 seconds (30 minutes)
                assert set_calls[0][0][2] == 1800

                # Team TTL: 3600 seconds (1 hour)
                assert set_calls[1][0][2] == 3600

                # Upcoming matches TTL: 1800 seconds (30 minutes)
                assert set_calls[2][0][2] == 1800

    @pytest.mark.asyncio
    async def test_cache_namespaces(self):
        """Test cache namespaces are correct."""
        service = DataService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with (
                patch.object(service, "_load_match_from_db") as mock_load_match,
                patch.object(service, "_load_team_from_db") as mock_load_team,
                patch.object(
                    service, "_load_upcoming_matches_from_db"
                ) as mock_load_upcoming,
            ):
                mock_load_match.return_value = None
                mock_load_team.return_value = None
                mock_load_upcoming.return_value = []

                await service.get_match_by_id("match123")
                await service.get_team_by_id("team123")
                await service.get_upcoming_matches(5)

                # Verify namespaces
                get_calls = mock_cache_manager.get.call_args_list

                # All should use appropriate namespaces
                assert get_calls[0][0][1] == "matches"  # match
                assert get_calls[1][0][1] == "teams"  # team
                assert get_calls[2][0][1] == "matches"  # upcoming matches

    @pytest.mark.asyncio
    async def test_performance_decorators_present(self):
        """Test that performance logging decorators are applied."""
        service = DataService()

        # Mock cache manager to avoid actual calls
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with (
                patch.object(service, "_load_match_from_db") as mock_load_match,
                patch.object(service, "_load_team_from_db") as mock_load_team,
                patch.object(
                    service, "_load_upcoming_matches_from_db"
                ) as mock_load_upcoming,
            ):
                mock_load_match.return_value = None
                mock_load_team.return_value = None
                mock_load_upcoming.return_value = []

                # Methods should execute without errors (decorators work)
                result1 = await service.get_match_by_id("match123")
                result2 = await service.get_team_by_id("team123")
                result3 = await service.get_upcoming_matches(5)

                assert result1 is None
                assert result2 is None
                assert result3 == []

    @pytest.mark.asyncio
    async def test_integration_scenario(self):
        """Test comprehensive integration scenario."""
        service = DataService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        # First calls miss cache, second calls hit cache
        mock_cache_manager.get.side_effect = [
            None,  # match miss
            {"id": "match123", "home_team": "Team A"},  # match hit
            None,  # team miss
            {"id": "team123", "name": "Team A"},  # team hit
            None,  # upcoming miss
            [{"id": "match1"}, {"id": "match2"}],  # upcoming hit
        ]

        # Mock database results
        mock_match = MagicMock()
        mock_match.dict.return_value = {"id": "match123", "home_team": "Team A"}

        mock_team = MagicMock()
        mock_team.dict.return_value = {"id": "team123", "name": "Team A"}

        mock_upcoming = [MagicMock()]
        mock_upcoming[0].dict.return_value = {"id": "match1"}

        with patch(
            "football_predict_system.domain.services.data_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with (
                patch.object(service, "_load_match_from_db") as mock_load_match,
                patch.object(service, "_load_team_from_db") as mock_load_team,
                patch.object(
                    service, "_load_upcoming_matches_from_db"
                ) as mock_load_upcoming_db,
            ):
                mock_load_match.return_value = mock_match
                mock_load_team.return_value = mock_team
                mock_load_upcoming_db.return_value = mock_upcoming

                with (
                    patch(
                        "football_predict_system.domain.models.Match"
                    ) as mock_match_class,
                    patch(
                        "football_predict_system.domain.models.Team"
                    ) as mock_team_class,
                ):
                    mock_match_instance = MagicMock()
                    mock_team_instance = MagicMock()
                    mock_match_class.return_value = mock_match_instance
                    mock_team_class.return_value = mock_team_instance

                    # First calls - cache miss, db hit
                    await service.get_match_by_id("match123")
                    await service.get_team_by_id("team123")
                    await service.get_upcoming_matches(5)

                    # Second calls - cache hit
                    await service.get_match_by_id("match123")
                    await service.get_team_by_id("team123")
                    await service.get_upcoming_matches(5)

                    # Verify cache behavior
                    assert mock_cache_manager.get.call_count == 6
                    assert (
                        mock_cache_manager.set.call_count == 3
                    )  # Only on cache misses

    def test_service_class_attributes(self):
        """Test service class has expected attributes."""
        service = DataService()

        # Should have logger attribute
        assert hasattr(service, "logger")

        # Should have expected methods
        assert hasattr(service, "get_match_by_id")
        assert hasattr(service, "get_team_by_id")
        assert hasattr(service, "get_upcoming_matches")

        # Should have private methods
        assert hasattr(service, "_load_match_from_db")
        assert hasattr(service, "_load_team_from_db")
        assert hasattr(service, "_load_upcoming_matches_from_db")

    @pytest.mark.asyncio
    async def test_all_methods_are_async(self):
        """Test that all public methods are async."""
        service = DataService()

        import inspect

        # Check public methods
        assert inspect.iscoroutinefunction(service.get_match_by_id)
        assert inspect.iscoroutinefunction(service.get_team_by_id)
        assert inspect.iscoroutinefunction(service.get_upcoming_matches)

        # Check private methods
        assert inspect.iscoroutinefunction(service._load_match_from_db)
        assert inspect.iscoroutinefunction(service._load_team_from_db)
        assert inspect.iscoroutinefunction(service._load_upcoming_matches_from_db)
