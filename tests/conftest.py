import os
import random

import pytest
from _pytest.config import Config
from _pytest.nodes import Item

try:
    import psycopg2
    from psycopg2 import OperationalError
except ImportError:
    psycopg2 = None  # type: ignore
    OperationalError = Exception  # type: ignore

# 设置固定种子确保测试可重现
SEED = int(os.getenv("TEST_SEED", "42"))
random.seed(SEED)

try:
    import numpy as np

    np.random.seed(SEED)
except ImportError:
    pass  # numpy not available, skip numpy seed setting

# 设置固定种子确保测试可重现
SEED = int(os.getenv("TEST_SEED", "42"))
random.seed(SEED)

try:
    import numpy as np

    np.random.seed(SEED)
except ImportError:
    pass  # numpy not available, skip numpy seed setting


def db_available() -> bool:
    """检测数据库是否可用, 1秒超时"""
    if psycopg2 is None:
        return False
    try:
        # Use environment variable or safe default for testing
        default_url = os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql://postgres:testpass@localhost:5432/sports_test",
        )
        db_url = os.environ.get("DATABASE_URL", default_url)
        conn = psycopg2.connect(db_url, connect_timeout=1)
        conn.close()
        return True
    except (OperationalError, Exception):
        return False


def pytest_configure(config: Config) -> None:
    """注册自定义标记"""
    config.addinivalue_line(
        "markers", "integration: tests requiring live database connection"
    )


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """根据环境变量决定是否跳过集成测试"""
    if os.environ.get("ENABLE_DB_TESTS") != "1":
        reason = "Integration tests disabled, set ENABLE_DB_TESTS=1 to enable"
        skip_integration = pytest.mark.skip(reason=reason)
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_runtest_setup(item: Item) -> None:
    """禁止网络访问, 除非标记 @pytest.mark.allow_network"""
    try:
        import pytest_socket

        pytest_socket.disable_socket()
    except ImportError:
        return  # pytest-socket not available, skip network isolation

    if any(mark.name == "allow_network" for mark in item.iter_markers()):
        pytest_socket.enable_socket()
