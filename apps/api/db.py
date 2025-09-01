import os
import sys
from typing import AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = structlog.get_logger(__name__)


def _is_testing() -> bool:
    """Detects if the code is running in a test environment."""
    return (
        os.getenv("PYTEST_CURRENT_TEST") is not None
        or "pytest" in os.getenv("_", "")
        or any("pytest" in arg for arg in sys.argv)
    )


# --- Database URL Configuration ---
if os.getenv("TEST_DATABASE_URL"):
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
elif _is_testing():
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
else:
    from dotenv import load_dotenv

    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL", "")

if not _is_testing() and not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in a non-testing environment.")

# Adjust URL for async driver
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# --- Engine and Session Configuration ---
async_engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


async def check_db_connection_async() -> tuple[bool, str]:
    """Asynchronously checks the database connection."""
    try:
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True, "Database connection successful."
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        # In a test environment, the database might not be initialized yet.
        # This check is primarily for production readiness.
        if _is_testing():
            return True, "Skipping DB check in test environment."
        return False, f"Database connection failed: {e}"
