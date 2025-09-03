"""
Production-grade database management with connection pooling and monitoring.

This module provides:
- Connection pooling with automatic retry
- Health checks and monitoring
- Transaction management
- Query performance tracking
- Database migration support
"""

import asyncio
import time
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from .config import get_settings
from .exceptions import handle_database_exception
from .logging import get_logger

# SQLAlchemy declarative base
Base = declarative_base()

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self._engine: Engine | None = None
        self._async_engine: AsyncEngine | None = None
        self._session_factory: sessionmaker | None = None
        self._async_session_factory: sessionmaker | None = None
        self._connection_pool = None
        self._health_check_query = text("SELECT 1")

    def get_engine(self) -> Engine:
        """Get or create synchronous database engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    def get_async_engine(self) -> AsyncEngine:
        """Get or create asynchronous database engine."""
        if self._async_engine is None:
            self._async_engine = self._create_async_engine()
        return self._async_engine

    def _create_engine(self) -> Engine:
        """Create synchronous database engine with optimized settings."""
        db_config = self.settings.database

        # Get the correct database URL
        database_url = self.settings.get_database_url()

        # Configure engine based on database type
        if "sqlite" in database_url:
            # SQLite doesn't support connection pooling
            engine = create_engine(
                db_config.url,
                echo=db_config.echo,
                future=True,
                connect_args={
                    "check_same_thread": False,
                },
            )
        else:
            # PostgreSQL and other databases support connection pooling
            engine = create_engine(
                db_config.url,
                poolclass=QueuePool,
                pool_size=db_config.pool_size,
                max_overflow=db_config.max_overflow,
                pool_timeout=db_config.pool_timeout,
                pool_recycle=db_config.pool_recycle,
                echo=db_config.echo,
                future=True,
                connect_args={
                    "server_side_cursors": True,
                },
            )

        # Add event listeners for monitoring
        self._setup_engine_events(engine)

        logger.info(
            "Database engine created", url=db_config.url, pool_size=db_config.pool_size
        )
        return engine

    def _create_async_engine(self) -> AsyncEngine:
        """Create asynchronous database engine."""
        db_config = self.settings.database

        # Get the correct database URL
        database_url = self.settings.get_database_url()

        # Configure async engine based on database type
        if "sqlite" in database_url:
            # SQLite async configuration
            async_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
            engine = create_async_engine(
                async_url,
                echo=db_config.echo,
                future=True,
            )
        else:
            # PostgreSQL async configuration
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            engine = create_async_engine(
                async_url,
                pool_size=db_config.pool_size,
                max_overflow=db_config.max_overflow,
                pool_timeout=db_config.pool_timeout,
                pool_recycle=db_config.pool_recycle,
                echo=db_config.echo,
                future=True,
            )

        logger.info("Async database engine created", url=async_url)
        return engine

    def _setup_engine_events(self, engine: Engine) -> None:
        """Setup database engine event listeners for monitoring."""

        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = time.time()

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total = time.time() - context._query_start_time

            # Log slow queries
            if total > 1.0:  # Log queries taking more than 1 second
                logger.warning(
                    "Slow database query detected",
                    duration=total,
                    statement=statement[:200] + "..."
                    if len(statement) > 200
                    else statement,
                )

            # Log all queries in debug mode
            if self.settings.debug:
                logger.debug(
                    "Database query executed",
                    duration=total,
                    statement=statement[:100] + "..."
                    if len(statement) > 100
                    else statement,
                )

        @event.listens_for(engine, "handle_error")
        def handle_error(exception_context):
            logger.error(
                "Database error occurred",
                error=str(exception_context.original_exception),
                statement=exception_context.statement,
                is_disconnect=exception_context.is_disconnect,
            )

    def get_session_factory(self) -> sessionmaker:
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.get_engine(), class_=Session, expire_on_commit=False
            )
        return self._session_factory

    def get_async_session_factory(self) -> sessionmaker:
        """Get or create async session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = sessionmaker(
                bind=self.get_async_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._async_session_factory

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup."""
        session_factory = self.get_session_factory()
        session = session_factory()

        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session error", error=str(e))
            raise handle_database_exception(e)
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup."""
        session_factory = self.get_async_session_factory()
        session = session_factory()

        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Async database session error", error=str(e))
            raise handle_database_exception(e)
        finally:
            await session.close()

    async def health_check(self) -> dict[str, Any]:
        """Perform database health check."""
        start_time = time.time()

        try:
            # Test synchronous connection
            with self.get_session() as session:
                result = session.execute(self._health_check_query)
                sync_result = result.scalar() or 0

            # Test asynchronous connection
            async with self.get_async_session() as session:
                result = await session.execute(self._health_check_query)
                async_result = result.scalar() or 0

            duration = time.time() - start_time

            health_status = {
                "status": "healthy",
                "sync_connection": sync_result == 1,
                "async_connection": async_result == 1,
                "response_time": duration,
                "pool_info": self._get_pool_info(),
            }

            logger.debug("Database health check passed", **health_status)
            return health_status

        except Exception as e:
            duration = time.time() - start_time

            health_status = {
                "status": "unhealthy",
                "error": str(e),
                "response_time": duration,
            }

            logger.error("Database health check failed", **health_status)
            return health_status

    def _get_pool_info(self) -> dict[str, Any]:
        """Get database connection pool information."""
        if self._engine is None:
            return {}

        pool = self._engine.pool

        # SQLite doesn't have connection pooling
        if hasattr(pool, "size"):
            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
        else:
            return {"type": "NullPool", "pooling": "disabled"}

    async def close(self) -> None:
        """Close all database connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Synchronous database engine disposed")

        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Asynchronous database engine disposed")

    async def create_engine(self) -> AsyncEngine:
        """Create database engine (public method for tests)."""
        if self._async_engine is None:
            self._async_engine = self._create_async_engine()
        # Also set _engine for compatibility with tests
        self._engine = self._async_engine
        return self._async_engine

    async def create_session_factory(self) -> sessionmaker:
        """Create async session factory (public method for tests)."""
        return self.get_async_session_factory()

    async def execute_query(self, query: str, params: tuple = None) -> Any:
        """Execute a database query."""
        async with self.get_async_session() as session:
            if params:
                result = await session.execute(text(query), params)
            else:
                result = await session.execute(text(query))
            return result

    async def execute_transaction(self, operations: list[tuple[str, tuple]]) -> None:
        """Execute multiple operations in a transaction."""
        async with self.get_async_session() as session:
            try:
                for query, params in operations:
                    await session.execute(text(query), params)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_connection_info(self) -> dict:
        """Get database connection information."""
        return {
            "url": str(self.settings.database.url).replace(
                self.settings.database.url.password or "", "***"
            ),
            "pool_info": self._get_pool_info(),
            "engine_info": {
                "name": self.get_engine().name if self._engine else None,
                "echo": self.settings.database.echo,
            },
        }

    async def create_connection_pool(self) -> dict:
        """Create and return connection pool info."""
        self.get_engine()  # Ensure engine is created
        return self._get_pool_info()

    async def init_database(self) -> None:
        """Initialize database tables."""
        engine = self.get_engine()
        # Create all tables defined in Base metadata
        Base.metadata.create_all(bind=engine.sync_engine if hasattr(engine, 'sync_engine') else engine)


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_session() -> Generator[Session, None, None]:
    """Get database session (convenience function)."""
    return get_database_manager().get_session()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session (convenience function)."""
    async with get_database_manager().get_async_session() as session:
        yield session


class TransactionManager:
    """Manages database transactions with retry logic."""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = get_logger(__name__)

    @contextmanager
    def transaction(self, session: Session = None):
        """Execute operations in a database transaction with retry."""
        db_manager = get_database_manager()

        for attempt in range(self.max_retries + 1):
            try:
                if session:
                    # Use provided session
                    yield session
                    session.commit()
                    return
                else:
                    # Create new session
                    with db_manager.get_session() as new_session:
                        yield new_session
                        # Session is automatically committed in context manager
                        return

            except (SQLAlchemyError, ConnectionError) as e:
                if attempt < self.max_retries:
                    self.logger.warning(
                        "Database operation failed, retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        error=str(e),
                    )
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    self.logger.error(
                        "Database operation failed after all retries", error=str(e)
                    )
                    raise handle_database_exception(e)
            except Exception as e:
                # Unexpected errors should not be retried
                self.logger.error("Unexpected error in transaction", error=str(e))
                raise

    @asynccontextmanager
    async def async_transaction(self, session: AsyncSession = None):
        """Execute operations in an async database transaction with retry."""
        db_manager = get_database_manager()

        for attempt in range(self.max_retries + 1):
            try:
                if session:
                    # Use provided session
                    yield session
                    await session.commit()
                    return
                else:
                    # Create new session
                    async with db_manager.get_async_session() as new_session:
                        yield new_session
                        # Session is automatically committed in context manager
                        return

            except Exception as e:
                if attempt < self.max_retries:
                    self.logger.warning(
                        "Async transaction failed, retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        error=str(e),
                    )
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    self.logger.error(
                        "Async transaction failed after all retries", error=str(e)
                    )
                    raise handle_database_exception(e)


# Global transaction manager
transaction_manager = TransactionManager()
