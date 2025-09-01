"""
缓存测试夹具

提供Redis客户端模拟、缓存清理等缓存测试所需的夹具。
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[AsyncMock, None]:
    """模拟Redis客户端"""
    mock_redis = AsyncMock()

    # 配置基础Redis操作
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.flushdb = AsyncMock(return_value=True)
    mock_redis.keys = AsyncMock(return_value=[])

    # 配置哈希操作
    mock_redis.hget = AsyncMock(return_value=None)
    mock_redis.hset = AsyncMock(return_value=1)
    mock_redis.hdel = AsyncMock(return_value=1)
    mock_redis.hgetall = AsyncMock(return_value={})

    # 配置列表操作
    mock_redis.lpush = AsyncMock(return_value=1)
    mock_redis.rpop = AsyncMock(return_value=None)
    mock_redis.llen = AsyncMock(return_value=0)

    yield mock_redis


@pytest.fixture
def clean_cache():
    """清理缓存"""
    # 测试前后清理缓存的逻辑
    yield
    # 这里可以添加实际的缓存清理逻辑


@pytest_asyncio.fixture
async def mock_cache_manager():
    """模拟缓存管理器"""
    with patch(
        "src.football_predict_system.core.cache.get_cache_manager"
    ) as mock_manager:
        manager_instance = AsyncMock()

        # 模拟Redis客户端
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        manager_instance.get_redis_client = AsyncMock(return_value=mock_redis)

        # 模拟缓存操作
        manager_instance.get = AsyncMock(return_value=None)
        manager_instance.set = AsyncMock(return_value=True)
        manager_instance.delete = AsyncMock(return_value=True)
        manager_instance.clear_namespace = AsyncMock(return_value=0)
        manager_instance.exists = AsyncMock(return_value=False)

        # 模拟健康检查
        manager_instance.health_check = AsyncMock(
            return_value={"status": "healthy", "latency": 0.005}
        )

        # 模拟关闭
        manager_instance.close = AsyncMock()

        mock_manager.return_value = manager_instance
        yield manager_instance


@pytest.fixture
def cache_test_data():
    """缓存测试数据"""
    return {
        "prediction_cache_key": "predictions:match_123",
        "model_cache_key": "models:xgboost_v1",
        "team_cache_key": "teams:team_456",
        "test_prediction": {
            "match_id": "123",
            "home_win_prob": 0.6,
            "draw_prob": 0.25,
            "away_win_prob": 0.15,
            "timestamp": "2024-01-01T12:00:00",
        },
        "test_model_info": {
            "name": "xgboost_v1",
            "version": "1.0.0",
            "accuracy": 0.85,
            "last_trained": "2024-01-01T00:00:00",
        },
    }
