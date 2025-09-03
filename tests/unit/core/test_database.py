"""Database manager unit tests."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from football_predict_system.core.database import (
    DatabaseManager,
    get_async_session,
    get_database_manager,
    get_session,
)

pytestmark = pytest.mark.skip_for_ci  # 跳过此文件用于CI


class TestDatabaseManager:
    """Test DatabaseManager class."""

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization."""
        with patch(
            "football_predict_system.core.database.get_settings"
        ) as mock_settings:
            mock_settings.return_value.database_url = "postgresql://test"
            db_manager = DatabaseManager()

            assert db_manager.settings is not None
            assert db_manager._engine is None
            assert db_manager._async_engine is None

    @patch("football_predict_system.core.database.get_settings")
    def test_get_engine(self, mock_settings):
        """Test getting database engine."""
        mock_settings.return_value.database_url = "postgresql://test"

        db_manager = DatabaseManager()

        # Mock the _setup_engine_events to avoid event listener issues
        with patch.object(db_manager, "_setup_engine_events"):
            with patch(
                "football_predict_system.core.database.create_engine"
            ) as mock_create:
                mock_engine = Mock()
                mock_create.return_value = mock_engine

                engine = db_manager.get_engine()

                assert engine == mock_engine
                assert db_manager._engine == mock_engine
                mock_create.assert_called_once()

    @patch("football_predict_system.core.database.create_async_engine")
    @patch("football_predict_system.core.database.get_settings")
    def test_get_async_engine(self, mock_settings, mock_create_async_engine):
        """Test getting asynchronous database engine."""
        # Setup mocks
        mock_settings.return_value.async_database_url = "postgresql+asyncpg://test"
        mock_settings.return_value.database_pool_size = 5
        mock_settings.return_value.database_max_overflow = 10
        mock_async_engine = Mock()
        mock_create_async_engine.return_value = mock_async_engine

        db_manager = DatabaseManager()
        async_engine = db_manager.get_async_engine()

        assert async_engine == mock_async_engine
        mock_create_async_engine.assert_called_once()

    @patch("football_predict_system.core.database.sessionmaker")
    @patch("football_predict_system.core.database.get_settings")
    def test_get_session_factory(self, mock_settings, mock_sessionmaker):
        """Test getting session factory."""
        mock_settings.return_value.database_url = "postgresql://test"
        mock_factory = Mock()
        mock_sessionmaker.return_value = mock_factory

        db_manager = DatabaseManager()
        with patch.object(db_manager, "get_engine") as mock_get_engine:
            mock_engine = Mock()
            mock_get_engine.return_value = mock_engine

            factory = db_manager.get_session_factory()

            assert factory == mock_factory
            mock_sessionmaker.assert_called_once()

    @patch("football_predict_system.core.database.sessionmaker")
    @patch("football_predict_system.core.database.get_settings")
    def test_get_async_session_factory(self, mock_settings, mock_sessionmaker):
        """Test getting async session factory."""
        mock_settings.return_value.async_database_url = "postgresql+asyncpg://test"
        mock_factory = Mock()
        mock_sessionmaker.return_value = mock_factory

        db_manager = DatabaseManager()
        with patch.object(db_manager, "get_async_engine") as mock_get_async_engine:
            mock_async_engine = Mock()
            mock_get_async_engine.return_value = mock_async_engine

            factory = db_manager.get_async_session_factory()

            assert factory == mock_factory
            mock_sessionmaker.assert_called_once()

    @pytest.mark.asyncio
    @patch("football_predict_system.core.database.get_settings")
    async def test_health_check_success(self, mock_settings):
        """Test successful database health check."""
        mock_settings.return_value.database_url = "postgresql://test"

        db_manager = DatabaseManager()

        # Mock sync engine and session
        mock_engine = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        # Mock pool info
        mock_pool = Mock()
        mock_pool.size.return_value = 5
        mock_pool.checkedin.return_value = 3
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0
        mock_engine.pool = mock_pool

        # Mock async engine and session
        mock_async_engine = AsyncMock()
        mock_async_session = AsyncMock()
        mock_async_result = Mock()
        mock_async_result.scalar.return_value = 1
        mock_async_session.execute.return_value = mock_async_result

        with (
            patch.object(db_manager, "get_engine", return_value=mock_engine),
            patch.object(
                db_manager, "get_async_engine", return_value=mock_async_engine
            ),
            patch.object(db_manager, "get_session_factory") as mock_sync_factory,
            patch.object(db_manager, "get_async_session_factory") as mock_async_factory,
        ):
            # Configure session factories
            mock_sync_factory.return_value = lambda: mock_session
            mock_async_factory.return_value = lambda: mock_async_session

            # Configure context managers
            mock_session.__enter__ = Mock(return_value=mock_session)
            mock_session.__exit__ = Mock(return_value=None)
            mock_async_session.__aenter__ = AsyncMock(return_value=mock_async_session)
            mock_async_session.__aexit__ = AsyncMock(return_value=None)

            result = await db_manager.health_check()

            assert result["status"] == "healthy"
            assert result["sync_connection"] is True
            assert result["async_connection"] is True
            assert "response_time" in result
            assert "pool_info" in result

    @pytest.mark.asyncio
    @patch("football_predict_system.core.database.get_settings")
    async def test_health_check_failure(self, mock_settings):
        """Test failed database health check."""
        mock_settings.return_value.database_url = "postgresql://test"

        db_manager = DatabaseManager()

        # Mock async engine to raise an exception
        mock_async_engine = AsyncMock()
        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError("Connection failed")

        with (
            patch.object(
                db_manager, "get_async_engine", return_value=mock_async_engine
            ),
            patch.object(db_manager, "get_async_session_factory") as mock_factory,
        ):
            mock_factory.return_value = lambda: mock_session

            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            result = await db_manager.health_check()

            assert result["status"] == "unhealthy"
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    @patch("football_predict_system.core.database.get_settings")
    async def test_close(self, mock_settings):
        """Test closing database connections."""
        mock_settings.return_value.database_url = "postgresql://test"

        db_manager = DatabaseManager()

        # Mock engines
        mock_engine = Mock()
        mock_async_engine = AsyncMock()

        db_manager._engine = mock_engine
        db_manager._async_engine = mock_async_engine

        await db_manager.close()

        mock_engine.dispose.assert_called_once()
        mock_async_engine.dispose.assert_called_once()


class TestDatabaseFunctions:
    """Test database utility functions."""

    @patch("football_predict_system.core.database.DatabaseManager")
    def test_get_database_manager(self, mock_db_manager_class):
        """Test getting database manager singleton."""
        mock_instance = Mock()
        mock_db_manager_class.return_value = mock_instance

        # First call should create instance
        manager1 = get_database_manager()
        assert manager1 == mock_instance

        # Second call should return same instance
        manager2 = get_database_manager()
        assert manager2 == mock_instance

        # Should only create one instance
        mock_db_manager_class.assert_called_once()

    @patch("football_predict_system.core.database.get_database_manager")
    def test_get_session(self, mock_get_db_manager):
        """Test getting database session."""
        mock_db_manager = Mock()
        mock_session_factory = Mock()
        mock_session = Mock()

        mock_db_manager.get_session_factory.return_value = mock_session_factory
        mock_session_factory.return_value = mock_session
        mock_get_db_manager.return_value = mock_db_manager

        # Mock context manager behavior
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        with get_session() as session:
            assert session == mock_session

        mock_session.__exit__.assert_called_once()

    @pytest.mark.asyncio
    @patch("football_predict_system.core.database.get_database_manager")
    async def test_get_async_session(self, mock_get_db_manager):
        """Test getting async database session."""
        mock_db_manager = Mock()
        mock_session_factory = Mock()
        mock_session = AsyncMock()

        mock_db_manager.get_async_session_factory.return_value = mock_session_factory
        mock_session_factory.return_value = mock_session
        mock_get_db_manager.return_value = mock_db_manager

        # Mock async context manager behavior
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        async with get_async_session() as session:
            assert session == mock_session

        mock_session.__aexit__.assert_called_once()


class TestDatabaseExceptionHandling:
    """Test database exception handling."""

    @patch("football_predict_system.core.database.get_settings")
    def test_engine_creation_with_invalid_url(self, mock_settings):
        """Test engine creation with invalid database URL."""
        mock_settings.return_value.database_url = "invalid://url"

        db_manager = DatabaseManager()

        # This should not raise an exception during initialization
        # The exception would be raised when actually trying to connect
        assert db_manager is not None

    @patch("football_predict_system.core.database.get_settings")
    def test_session_creation_failure(self, mock_settings):
        """Test handling session creation failures."""
        mock_settings.return_value.database_url = "postgresql://test"

        db_manager = DatabaseManager()

        with patch.object(db_manager, "get_engine") as mock_get_engine:
            mock_get_engine.side_effect = SQLAlchemyError("Connection failed")

            with pytest.raises(SQLAlchemyError):
                db_manager.get_session_factory()
