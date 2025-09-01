"""
API测试夹具

提供异步HTTP客户端、模拟应用等API测试所需的夹具。
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient

from src.football_predict_system.main import app


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步HTTP测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_client() -> AsyncGenerator[AsyncClient, None]:
    """带认证的异步HTTP客户端"""
    headers = {"Authorization": "Bearer test_token"}
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers=headers
    ) as client:
        yield client


@pytest.fixture
def mock_app() -> FastAPI:
    """模拟的FastAPI应用实例"""
    with patch(
        "src.football_predict_system.core.config.get_settings"
    ) as mock_settings, patch(
        "src.football_predict_system.core.database.get_database_manager"
    ) as mock_db, patch(
        "src.football_predict_system.core.cache.get_cache_manager"
    ) as mock_cache, patch(
        "src.football_predict_system.core.health.get_health_checker"
    ) as mock_health:

        # 配置模拟设置
        settings = MagicMock()
        settings.app_name = "Test Football Prediction System"
        settings.app_version = "0.1.0"
        settings.debug = True
        settings.environment.value = "testing"

        api_config = MagicMock()
        api_config.cors_origins = ["*"]
        api_config.cors_credentials = True
        api_config.cors_methods = ["*"]
        api_config.cors_headers = ["*"]
        settings.api = api_config

        mock_settings.return_value = settings

        # 配置模拟数据库管理器
        db_manager = MagicMock()
        db_manager.get_engine.return_value = MagicMock()
        db_manager.get_async_engine.return_value = MagicMock()
        db_manager.close = AsyncMock()
        mock_db.return_value = db_manager

        # 配置模拟缓存管理器
        cache_manager = AsyncMock()
        cache_manager.get_redis_client = AsyncMock(return_value=MagicMock())
        cache_manager.close = AsyncMock()
        mock_cache.return_value = cache_manager

        # 配置模拟健康检查器
        health_checker = MagicMock()
        health_response = MagicMock()
        health_response.status = "healthy"
        health_response.model_dump.return_value = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00",
            "components": [
                {"name": "database", "status": "healthy"},
                {"name": "redis", "status": "healthy"}
            ],
            "uptime": 123.45,
            "version": "0.1.0"
        }
        health_checker.get_system_health = AsyncMock(
            return_value=health_response
        )
        mock_health.return_value = health_checker

        yield app


@pytest_asyncio.fixture
async def concurrent_clients(
    request: Any,
) -> AsyncGenerator[list[AsyncClient], None]:
    """创建多个并发客户端用于负载测试"""
    client_count = getattr(request, 'param', 5)
    clients = []

    for _ in range(client_count):
        client = AsyncClient(app=app, base_url="http://test")
        clients.append(client)

    yield clients

    # 清理客户端
    for client in clients:
        await client.aclose()


@pytest.fixture
def mock_prediction_service():
    """模拟预测服务"""
    service_path = "src.football_predict_system.domain.services.PredictionService"
    with patch(service_path) as mock_service:
        service_instance = MagicMock()

        # 模拟异步方法
        service_instance.generate_prediction = AsyncMock(
            return_value={
                "prediction_id": "test_123",
                "home_team_win_probability": 0.45,
                "draw_probability": 0.30,
                "away_team_win_probability": 0.25,
                "confidence": 0.85
            }
        )

        service_instance.generate_batch_predictions = AsyncMock(
            return_value=[
                {"match_id": "1", "prediction": "home_win"},
                {"match_id": "2", "prediction": "draw"}
            ]
        )

        mock_service.return_value = service_instance
        yield service_instance


@pytest.fixture
def mock_model_service():
    """模拟模型服务"""
    service_path = "src.football_predict_system.domain.services.ModelService"
    with patch(service_path) as mock_service:
        service_instance = MagicMock()

        service_instance.get_available_models = AsyncMock(
            return_value=[
                {"name": "xgboost_v1", "version": "1.0.0", "accuracy": 0.85},
                {
                    "name": "neural_net_v1",
                    "version": "1.0.0",
                    "accuracy": 0.87
                }
            ]
        )

        service_instance.get_default_model = AsyncMock(
            return_value={"name": "xgboost_v1", "version": "1.0.0"}
        )

        mock_service.return_value = service_instance
        yield service_instance


@pytest_asyncio.fixture
async def performance_timer():
    """性能测试计时器"""
    timers = {}

    def start_timer(name: str):
        timers[name] = asyncio.get_event_loop().time()

    def end_timer(name: str) -> float:
        if name not in timers:
            raise ValueError(f"Timer {name} not started")
        return asyncio.get_event_loop().time() - timers[name]

    class Timer:
        start = start_timer
        end = end_timer

    yield Timer()
