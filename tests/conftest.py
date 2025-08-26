import os

import psycopg2
import pytest
from psycopg2 import OperationalError


def db_available():
    """检测数据库是否可用，1秒超时"""
    try:
        default_url = "postgresql://postgres:password@localhost:5432/sports"
        db_url = os.environ.get("DATABASE_URL", default_url)
        conn = psycopg2.connect(db_url, connect_timeout=1)
        conn.close()
        return True
    except (OperationalError, Exception):
        return False


def pytest_configure(config):
    """注册自定义标记"""
    config.addinivalue_line("markers", "integration: tests requiring live database connection")


def pytest_collection_modifyitems(config, items):
    """根据环境变量决定是否跳过集成测试"""
    if os.environ.get("ENABLE_DB_TESTS") != "1":
        reason = "Integration tests disabled, set ENABLE_DB_TESTS=1 to enable"
        skip_integration = pytest.mark.skip(reason=reason)
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
