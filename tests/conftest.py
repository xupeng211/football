"""
全局测试配置

配置pytest异步测试、夹具和标记。
"""

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
    config.addinivalue_line("markers", "unit: 快速单元测试")
    config.addinivalue_line("markers", "integration: 需要外部依赖的集成测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "slow: 慢速测试 (>10秒)")
    config.addinivalue_line("markers", "fast: 快速测试 (<1秒)")
    config.addinivalue_line("markers", "api: API相关测试")
    config.addinivalue_line("markers", "database: 数据库相关测试")
    config.addinivalue_line("markers", "cache: 缓存相关测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "concurrent: 并发测试")


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """根据环境变量决定是否跳过特定测试"""
    # 跳过集成测试
    if os.environ.get("ENABLE_DB_TESTS") != "1":
        reason = "Integration tests disabled, set ENABLE_DB_TESTS=1 to enable"
        skip_integration = pytest.mark.skip(reason=reason)
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

    # 跳过慢速测试
    if os.environ.get("ENABLE_SLOW_TESTS") != "1":
        reason = "Slow tests disabled, set ENABLE_SLOW_TESTS=1 to enable"
        skip_slow = pytest.mark.skip(reason=reason)
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_runtest_setup(item: Item) -> None:
    """设置测试运行环境"""
    # 禁止网络访问, 除非标记 @pytest.mark.allow_network
    try:
        import pytest_socket

        pytest_socket.disable_socket()

        if any(mark.name == "allow_network" for mark in item.iter_markers()):
            pytest_socket.enable_socket()
    except ImportError:
        pass  # pytest-socket not available, skip network isolation


# 性能测试相关的夹具
@pytest.fixture
def benchmark_config():
    """基准测试配置"""
    return {
        "max_response_time": 1.0,  # 最大响应时间(秒)
        "min_requests_per_second": 100,  # 最小每秒请求数
        "concurrent_users": 10,  # 并发用户数
        "test_duration": 30,  # 测试持续时间(秒)
    }


@pytest.fixture
def test_environment():
    """测试环境信息"""
    return {
        "environment": os.getenv("TEST_ENV", "local"),
        "database_available": db_available(),
        "enable_db_tests": os.getenv("ENABLE_DB_TESTS") == "1",
        "enable_slow_tests": os.getenv("ENABLE_SLOW_TESTS") == "1",
        "enable_network": os.getenv("ENABLE_NETWORK_TESTS") == "1",
    }


# 清理夹具
@pytest.fixture(autouse=True)
def cleanup_environment():
    """自动清理测试环境"""
    # 测试前设置
    return
    # 测试后清理
    # 这里可以添加清理逻辑
