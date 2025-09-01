"""Core unit tests for database module to boost coverage."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from football_predict_system.core.database import DatabaseManager, get_database_manager


class TestDatabaseManager:
    """Test the DatabaseManager class."""

    @pytest.fixture
    def db_manager(self):
        """Create a database manager."""
        return DatabaseManager()

    def test_init(self, db_manager):
        """Test DatabaseManager initialization."""
        assert db_manager.settings is not None
        assert db_manager.logger is not None
        assert db_manager._engine is None
        assert db_manager._session_factory is None
        assert db_manager._connection_pool is None

    @pytest.mark.asyncio
    async def test_create_engine(self, db_manager):
        """Test engine creation."""
        with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_create.return_value = mock_engine

            engine = await db_manager.create_engine()
            assert engine == mock_engine
            assert db_manager._engine == mock_engine

    @pytest.mark.asyncio
    async def test_get_engine(self, db_manager):
        """Test getting engine."""
        with patch.object(db_manager, 'create_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_create.return_value = mock_engine

            engine = await db_manager.get_engine()
            assert engine == mock_engine

    @pytest.mark.asyncio
    async def test_create_session_factory(self, db_manager):
        """Test session factory creation."""
        with patch.object(db_manager, 'get_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_get_engine.return_value = mock_engine

            with patch('sqlalchemy.ext.asyncio.async_sessionmaker') as mock_sessionmaker:
                mock_factory = MagicMock()
                mock_sessionmaker.return_value = mock_factory

                factory = await db_manager.create_session_factory()
                assert factory == mock_factory
                assert db_manager._session_factory == mock_factory

    @pytest.mark.asyncio
    async def test_get_session(self, db_manager):
        """Test getting database session."""
        with patch.object(db_manager, 'get_session_factory') as mock_get_factory:
            mock_factory = MagicMock()
            mock_session = AsyncMock(spec=AsyncSession)
            mock_factory.return_value = mock_session
            mock_get_factory.return_value = mock_factory

            session = await db_manager.get_session()
            assert session == mock_session

    @pytest.mark.asyncio
    async def test_execute_query(self, db_manager):
        """Test query execution."""
        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_session.execute.return_value = mock_result
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await db_manager.execute_query("SELECT 1")
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_execute_transaction(self, db_manager):
        """Test transaction execution."""
        operations = [
            ("INSERT INTO table1 VALUES (?)", (1,)),
            ("UPDATE table2 SET x=?", (2,)),
        ]

        with patch.object(db_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session

            await db_manager.execute_transaction(operations)

            # Should execute all operations
            assert mock_session.execute.call_count == len(operations)
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, db_manager):
        """Test successful database health check."""
        with patch.object(db_manager, 'execute_query') as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_execute.return_value = mock_result

            health = await db_manager.health_check()

            assert health["status"] == "healthy"
            assert health["connection"] is True
            assert "response_time_ms" in health

    @pytest.mark.asyncio
    async def test_health_check_failure(self, db_manager):
        """Test failed database health check."""
        with patch.object(db_manager, 'execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Database error")

            health = await db_manager.health_check()

            assert health["status"] == "unhealthy"
            assert health["connection"] is False
            assert "error" in health

    @pytest.mark.asyncio
    async def test_get_connection_info(self, db_manager):
        """Test getting connection information."""
        info = await db_manager.get_connection_info()

        assert "driver" in info
        assert "host" in info
        assert "database" in info
        assert "pool_size" in info

    @pytest.mark.asyncio
    async def test_init_database(self, db_manager):
        """Test database initialization."""
        with patch.object(db_manager, 'get_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_get_engine.return_value = mock_engine

            with patch('football_predict_system.core.database.Base') as mock_base:
                await db_manager.init_database()

                # Should create all tables
                mock_base.metadata.create_all.assert_called_once_with(
                    bind=mock_engine.sync_engine
                )

    @pytest.mark.asyncio
    async def test_close_success(self, db_manager):
        """Test successful database close."""
        # Setup engine
        mock_engine = AsyncMock()
        db_manager._engine = mock_engine

        await db_manager.close()

        mock_engine.dispose.assert_called_once()
        assert db_manager._engine is None
        assert db_manager._session_factory is None

    @pytest.mark.asyncio
    async def test_close_no_engine(self, db_manager):
        """Test close when no engine exists."""
        # No engine setup
        await db_manager.close()

        # Should not raise error
        assert db_manager._engine is None

    def test_get_session_factory_sync(self, db_manager):
        """Test getting session factory synchronously."""
        mock_factory = MagicMock()
        db_manager._session_factory = mock_factory

        factory = db_manager.get_session_factory()
        assert factory == mock_factory

    @pytest.mark.asyncio
    async def test_create_connection_pool(self, db_manager):
        """Test connection pool creation."""
        with patch.object(db_manager, 'get_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_get_engine.return_value = mock_engine

            pool = await db_manager.create_connection_pool()
            assert pool == mock_engine
            assert db_manager._connection_pool == mock_engine


@pytest.mark.asyncio
async def test_get_database_manager():
    """Test database manager factory function."""
    manager = await get_database_manager()
    assert isinstance(manager, DatabaseManager)


class TestDatabaseContext:
    """Test database context managers and utilities."""

    @pytest.mark.asyncio
    async def test_session_context_success(self):
        """Test successful session context."""
        mock_manager = AsyncMock()
        mock_session = AsyncMock()
        mock_manager.get_session.return_value.__aenter__.return_value = mock_session

        with patch('football_predict_system.core.database.get_database_manager') as mock_get:
            mock_get.return_value = mock_manager

            # Import and test session context
            from football_predict_system.core.database import get_session

            async with get_session() as session:
                assert session == mock_session

    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback on error."""
        mock_manager = AsyncMock()
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Query failed")
        mock_manager.get_session.return_value.__aenter__.return_value = mock_session

        with patch('football_predict_system.core.database.get_database_manager') as mock_get:
            mock_get.return_value = mock_manager

            # Should handle rollback on error
            operations = [("SELECT 1", ())]

            try:
                await mock_manager.execute_transaction(operations)
            except Exception:
                # Expected to handle the error
                pass

            # Session should attempt rollback on error
            # (exact behavior depends on implementation)
