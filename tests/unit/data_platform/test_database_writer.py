"""
Tests for database writer functionality.

Tests the DatabaseWriter class for data platform storage operations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from football_predict_system.data_platform.storage.database_writer import (
    DatabaseWriter,
    UpsertResult,
)
from football_predict_system.domain.models import Match, Team


class TestUpsertResult:
    """Test UpsertResult model."""

    def test_initialization(self):
        """Test UpsertResult initialization."""
        result = UpsertResult()
        assert result.inserted == 0
        assert result.updated == 0
        assert result.failed == 0

    def test_with_values(self):
        """Test UpsertResult with specific values."""
        result = UpsertResult(inserted=80, updated=20, failed=2)
        assert result.inserted == 80
        assert result.updated == 20
        assert result.failed == 2

    def test_records_processed_property(self):
        """Test records processed calculation."""
        result = UpsertResult(inserted=80, updated=20)
        assert result.records_processed == 100


class TestDatabaseWriter:
    """Test DatabaseWriter functionality."""

    def test_initialization(self):
        """Test DatabaseWriter initialization."""
        writer = DatabaseWriter()

        assert writer.logger is not None
        assert hasattr(writer, "db_manager")
        # DatabaseWriter uses db_manager from get_database_manager()

    @pytest.mark.skip(reason="DatabaseWriter no longer has _create_session method")
    async def test_create_session(self):
        """Test session creation - DEPRECATED."""
        # This test is for a method that no longer exists
        # DatabaseWriter now uses db_manager for session management
        pass

    def test_validate_team_data(self):
        """Test team data validation."""
        writer = DatabaseWriter()

        # Valid team
        valid_team = Team(
            external_api_id=1, name="Test Team", short_name="TT", tla="TT"
        )
        assert writer._validate_team(valid_team) is True

        # Test with None
        assert writer._validate_team(None) is False

    def test_validate_match_data(self):
        """Test match data validation."""
        writer = DatabaseWriter()

        # Valid match
        valid_match = Match(
            external_api_id=1,
            home_team_id=1,
            away_team_id=2,
            match_date=datetime.now(),
            competition_id=1,
            status="FINISHED",
        )
        assert writer._validate_match(valid_match) is True

        # Test with None
        assert writer._validate_match(None) is False

    @pytest.mark.asyncio
    async def test_upsert_teams_success(self):
        """Test successful team upsert operation."""
        writer = DatabaseWriter()

        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        # Mock team creation/update
        with patch.object(writer, "_create_session", return_value=mock_session):
            with patch.object(writer, "_upsert_team", return_value=True) as mock_upsert:
                teams = [
                    Team(external_api_id=1, name="Team 1", short_name="T1", tla="T1"),
                    Team(external_api_id=2, name="Team 2", short_name="T2", tla="T2"),
                ]

                result = await writer.upsert_teams(teams)

                assert result.records_processed == 2
                assert mock_upsert.call_count == 2
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_teams_with_errors(self):
        """Test team upsert with some errors."""
        writer = DatabaseWriter()

        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        # Mock one success, one failure
        def mock_upsert_side_effect(*args):
            if args[1].external_api_id == 1:
                return True
            else:
                raise Exception("Database error")

        with patch.object(writer, "_create_session", return_value=mock_session):
            with patch.object(
                writer, "_upsert_team", side_effect=mock_upsert_side_effect
            ):
                teams = [
                    Team(external_api_id=1, name="Team 1", short_name="T1", tla="T1"),
                    Team(external_api_id=2, name="Team 2", short_name="T2", tla="T2"),
                ]

                result = await writer.upsert_teams(teams)

                assert result.records_processed == 2
                assert result.errors == 1

    @pytest.mark.asyncio
    async def test_upsert_matches_success(self):
        """Test successful match upsert operation."""
        writer = DatabaseWriter()

        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        with patch.object(writer, "_create_session", return_value=mock_session):
            with patch.object(
                writer, "_upsert_match", return_value=True
            ) as mock_upsert:
                matches = [
                    Match(
                        external_api_id=1,
                        home_team_id=1,
                        away_team_id=2,
                        match_date=datetime.now(),
                        competition_id=1,
                        status="FINISHED",
                    ),
                    Match(
                        external_api_id=2,
                        home_team_id=3,
                        away_team_id=4,
                        match_date=datetime.now(),
                        competition_id=1,
                        status="FINISHED",
                    ),
                ]

                result = await writer.upsert_matches(matches)

                assert result.records_processed == 2
                assert mock_upsert.call_count == 2
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_error_handling(self):
        """Test proper error handling and session cleanup."""
        writer = DatabaseWriter()

        # Mock session that raises an error
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("Database error"))
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        with patch.object(writer, "_create_session", return_value=mock_session):
            with patch.object(writer, "_upsert_team", return_value=True):
                teams = [
                    Team(external_api_id=1, name="Team 1", short_name="T1", tla="T1")
                ]

                result = await writer.upsert_teams(teams)

                # Should handle error gracefully
                assert result.errors > 0
                mock_session.rollback.assert_called_once()
                mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_data_quality_stats(self):
        """Test data quality statistics retrieval."""
        writer = DatabaseWriter()

        # Mock session and query results
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        # Mock scalar queries
        mock_session.scalar = AsyncMock()
        mock_session.scalar.side_effect = [100, 50, 25]  # matches, teams, competitions

        with patch.object(writer, "_create_session", return_value=mock_session):
            stats = await writer.get_data_quality_stats()

            assert "total_matches" in stats
            assert "teams_count" in stats
            assert "competitions_count" in stats
            assert stats["total_matches"] == 100
            assert stats["teams_count"] == 50
            assert stats["competitions_count"] == 25

    @pytest.mark.asyncio
    async def test_log_collection_run(self):
        """Test collection run logging."""
        writer = DatabaseWriter()

        # Mock session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        with patch.object(writer, "_create_session", return_value=mock_session):
            await writer.log_collection_run(
                source="test_source", operation="test_operation", stats={"records": 100}
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_create_stats_from_counts(self):
        """Test stats creation from counts."""
        writer = DatabaseWriter()

        stats = writer._create_stats(processed=100, created=80, updated=20, errors=5)

        assert stats.records_processed == 100
        assert stats.records_created == 80
        assert stats.records_updated == 20
        assert stats.errors == 5
        assert stats.total == 100

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing of large datasets."""
        writer = DatabaseWriter()

        # Create large dataset
        teams = []
        for i in range(150):  # More than typical batch size
            teams.append(
                Team(
                    external_api_id=i,
                    name=f"Team {i}",
                    short_name=f"T{i}",
                    tla=f"T{i:02d}"[:3],
                )
            )

        # Mock session
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        with patch.object(writer, "_create_session", return_value=mock_session):
            with patch.object(writer, "_upsert_team", return_value=True) as mock_upsert:
                result = await writer.upsert_teams(teams)

                assert result.records_processed == 150
                assert mock_upsert.call_count == 150

    @pytest.mark.asyncio
    async def test_validation_filtering(self):
        """Test that invalid data is filtered out."""
        writer = DatabaseWriter()

        # Mix of valid and invalid teams
        teams = [
            Team(external_api_id=1, name="Valid Team", short_name="VT", tla="VT"),
            None,  # Invalid
            Team(external_api_id=2, name="Another Valid", short_name="AV", tla="AV"),
        ]

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        with patch.object(writer, "_create_session", return_value=mock_session):
            with patch.object(writer, "_upsert_team", return_value=True) as mock_upsert:
                result = await writer.upsert_teams(teams)

                # Should only process valid teams
                assert mock_upsert.call_count == 2
                assert result.records_processed == 2
                assert result.errors == 0  # Invalid data filtered, not counted as error


class TestDatabaseWriterIntegration:
    """Integration-style tests with less mocking."""

    @pytest.mark.asyncio
    async def test_stats_calculation(self):
        """Test proper statistics calculation."""
        writer = DatabaseWriter()

        # Test the _create_stats method directly
        stats = writer._create_stats(processed=100, created=60, updated=35, errors=5)

        assert stats.records_processed == 100
        assert stats.records_created == 60
        assert stats.records_updated == 35
        assert stats.errors == 5
        assert stats.total == 95  # created + updated

    def test_validation_logic(self):
        """Test validation logic without mocks."""
        writer = DatabaseWriter()

        # Test various team validation scenarios
        valid_team = Team(
            external_api_id=1, name="Arsenal", short_name="Arsenal", tla="ARS"
        )
        assert writer._validate_team(valid_team) is True

        # Test various match validation scenarios
        valid_match = Match(
            external_api_id=1,
            home_team_id=1,
            away_team_id=2,
            match_date=datetime(2024, 1, 1),
            competition_id=1,
            status="FINISHED",
        )
        assert writer._validate_match(valid_match) is True
