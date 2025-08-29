import os
import sys

import structlog
from sqlalchemy import create_engine, text
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


# 在测试环境中使用内存数据库, 否则使用环境变量
if _is_testing():
    DATABASE_URL = "sqlite:///:memory:"
else:
    from dotenv import load_dotenv

    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

engine = create_engine(DATABASE_URL)


def check_db_connection() -> tuple[bool, str]:
    """Checks the database connection."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection successful."
    except SQLAlchemyError as e:
        logger.error("Database connection failed", error=str(e))
        return False, f"Database connection failed: {e}"
        return False, f"Database connection failed: {e}"
