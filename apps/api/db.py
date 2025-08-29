import os
import sys

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = structlog.get_logger(__name__)


# 检测是否在测试环境中运行
def _is_testing() -> bool:
    """检测是否在测试环境中运行"""
    return (
        os.getenv("PYTEST_CURRENT_TEST") is not None
        or "pytest" in os.getenv("_", "")
        or any("pytest" in arg for arg in sys.argv)
    )


# 优先使用测试数据库URL, 然后检查测试环境, 最后使用生产配置
if os.getenv("TEST_DATABASE_URL"):
    DATABASE_URL = os.getenv("TEST_DATABASE_URL")
elif _is_testing():
    DATABASE_URL = "sqlite:///:memory:"
else:
    from dotenv import load_dotenv

    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

# 如果在非测试环境中DATABASE_URL未设置, 则抛出错误
if not _is_testing() and not os.getenv("TEST_DATABASE_URL") and not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in a non-testing environment.")


engine: Engine | None = None


def init_db(database_url: str | None = None) -> None:
    """Initializes the database engine."""
    global engine
    if database_url:
        url = database_url
    else:
        if os.getenv("TEST_DATABASE_URL"):
            url = os.getenv("TEST_DATABASE_URL")
        elif _is_testing():
            url = "sqlite:///:memory:"
        else:
            from dotenv import load_dotenv

            load_dotenv()
            url = os.getenv("DATABASE_URL")

    if not url:
        raise ValueError("Database URL is not configured.")

    # In local development, the API runs on the host while the DB is in Docker.
    # We need to replace the service name 'db' with 'localhost'.
    if os.getenv("ENV") == "development":
        url = url.replace("db:", "localhost:")

    engine = create_engine(url)


def check_db_connection() -> tuple[bool, str]:
    """Checks the database connection."""
    if engine is None:
        # If in a test environment, initialize a default DB for health check.
        if _is_testing() or os.getenv("TEST_DATABASE_URL"):
            init_db()
        else:
            return False, "Database engine not initialized."

    try:
        # The engine might still be None if init_db() was called but failed
        if engine is None:
            return False, "Database engine failed to initialize."
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection successful."
    except SQLAlchemyError as e:
        logger.error("Database connection failed", error=str(e))
        return False, f"Database connection failed: {e}"
