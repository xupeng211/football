"""
迁移自test_api_simple.py的异步API测试

这些测试已从同步TestClient迁移到异步AsyncClient。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import asgi_lifespan
import httpx
import pytest
from httpx import AsyncClient


@pytest.mark.unit
@pytest.mark.api
class TestMigratedAPIEndpoints:
    """从test_api_simple.py迁移的异步API测试"""

    @pytest.fixture
    async def async_client(self):
        """异步HTTP客户端"""
        # 模拟所有外部依赖
        with patch(
            "src.football_predict_system.core.config.Settings"
        ) as MockSettings, patch(
            "src.football_predict_system.core.config.get_settings"
        ) as mock_get_settings, patch(
            "src.football_predict_system.core.database.get_database_manager"
        ) as mock_db, patch(
            "src.football_predict_system.core.cache.get_cache_manager"
        ) as mock_cache, patch(
            "src.football_predict_system.core.health.get_health_checker"
        ) as mock_health, patch(
            "src.football_predict_system.core.logging.setup_logging"
        ), patch(
            "src.football_predict_system.core.logging.get_logger"
        ):
            # 配置模拟设置
            mock_settings = MagicMock()
            mock_settings.app_name = "Football Prediction System"
            mock_settings.app_version = "1.0.0"
            mock_settings.debug = False
            mock_settings.environment.value = "testing"

            # API配置
            api_config = MagicMock()
            api_config.cors_origins = ["*"]
            api_config.cors_credentials = True
            api_config.cors_methods = ["*"]
            api_config.cors_headers = ["*"]
            mock_settings.api = api_config

            MockSettings.return_value = mock_settings
            mock_get_settings.return_value = mock_settings

            # 模拟数据库管理器
            mock_db_manager = MagicMock()
            mock_db_manager.get_engine.return_value = MagicMock()
            mock_db_manager.get_async_engine.return_value = MagicMock()
            mock_db_manager.close = AsyncMock()
            mock_db.return_value = mock_db_manager

            # 模拟缓存管理器
            mock_cache_manager = AsyncMock()
            mock_cache_manager.get_redis_client = AsyncMock(
                return_value=MagicMock()
            )
            mock_cache_manager.close = AsyncMock()
            mock_cache.return_value = mock_cache_manager

            # 模拟健康检查器
            mock_health_checker = MagicMock()
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
                "version": "1.0.0"
            }
            mock_health_checker.get_system_health = AsyncMock(
                return_value=health_response
            )
            mock_health.return_value = mock_health_checker

            # 导入并创建异步客户端
            from src.football_predict_system.main import app

            # 使用asgi-lifespan管理应用生命周期
            async with asgi_lifespan.LifespanManager(app):
                async with AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://test"
                ) as client:
                    yield client

    async def test_health_endpoint_migrated(self, async_client: AsyncClient):
        """测试健康检查端点（已迁移到异步）"""
        response = await async_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    async def test_root_endpoint_migrated(self, async_client: AsyncClient):
        """测试根端点（已迁移到异步）"""
        response = await async_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data

    async def test_api_status_endpoint_migrated(self, async_client: AsyncClient):
        """测试API状态端点（已迁移到异步）"""
        response = await async_client.get("/api/v1/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "v1"

    # 异步特有的测试 - 并发测试
    @pytest.mark.concurrent
    async def test_concurrent_api_calls(self, async_client: AsyncClient):
        """测试并发API调用（异步测试特有）"""
        import asyncio

        # 同时发起多个请求
        tasks = [
            async_client.get("/health"),
            async_client.get("/"),
            async_client.get("/api/v1/status")
        ]

        responses = await asyncio.gather(*tasks)

        # 验证所有响应都成功
        for response in responses:
            assert response.status_code == 200

    # 性能测试
    @pytest.mark.performance
    async def test_response_time_migrated(self, async_client: AsyncClient):
        """测试响应时间（异步性能测试）"""
        import time

        start_time = time.time()
        response = await async_client.get("/health")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # 应在1秒内响应


# 导入测试（保持同步，因为不涉及HTTP请求）
@pytest.mark.unit
def test_app_import_migrated():
    """测试API应用导入（保持同步）"""
    with patch(
        "src.football_predict_system.core.config.Settings"
    ) as MockSettings, patch(
        "src.football_predict_system.core.logging.setup_logging"
    ), patch(
        "src.football_predict_system.core.logging.get_logger"
    ):
        mock_settings = MagicMock()
        mock_settings.app_name = "Football Prediction System"
        MockSettings.return_value = mock_settings

        from src.football_predict_system.main import app

        assert app is not None
        assert hasattr(app, "title")


@pytest.mark.unit
def test_api_router_import_migrated():
    """测试API路由导入（保持同步）"""
    with patch(
        "src.football_predict_system.core.logging.get_logger"
    ):
        from src.football_predict_system.api.v1.endpoints import router

        assert router is not None
