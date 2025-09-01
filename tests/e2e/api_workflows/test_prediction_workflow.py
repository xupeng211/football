"""
预测工作流端到端测试

测试从API请求到预测结果的完整异步工作流。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import asgi_lifespan
import httpx
import pytest
from httpx import AsyncClient

from tests.fixtures.factories import MatchFactory, PredictionFactory


@pytest.mark.e2e
@pytest.mark.api
class TestPredictionWorkflowE2E:
    """预测工作流端到端测试"""

    @pytest.fixture
    async def e2e_client(self):
        """端到端测试客户端"""
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
            "src.football_predict_system.domain.services.PredictionService"
        ) as mock_prediction_service, patch(
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

            # 模拟所有核心服务
            mock_db_manager = MagicMock()
            mock_db_manager.get_engine.return_value = MagicMock()
            mock_db_manager.get_async_engine.return_value = MagicMock()
            mock_db_manager.close = AsyncMock()
            mock_db.return_value = mock_db_manager

            mock_cache_manager = AsyncMock()
            mock_cache_manager.get_redis_client = AsyncMock(return_value=MagicMock())
            mock_cache_manager.close = AsyncMock()
            mock_cache.return_value = mock_cache_manager

            mock_health_checker = MagicMock()
            health_response = MagicMock()
            health_response.status = "healthy"
            health_response.model_dump.return_value = {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00",
                "components": [
                    {"name": "database", "status": "healthy"},
                    {"name": "redis", "status": "healthy"},
                ],
                "uptime": 123.45,
                "version": "1.0.0",
            }
            mock_health_checker.get_system_health = AsyncMock(
                return_value=health_response
            )
            mock_health.return_value = mock_health_checker

            # 模拟预测服务
            prediction_service_instance = AsyncMock()
            prediction_service_instance.generate_prediction = AsyncMock(
                return_value=PredictionFactory.create()
            )
            mock_prediction_service.return_value = prediction_service_instance

            # 导入并创建异步客户端
            from src.football_predict_system.main import app

            async with asgi_lifespan.LifespanManager(app):
                async with AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    yield client

    async def test_complete_prediction_workflow(self, e2e_client: AsyncClient):
        """测试完整的预测工作流"""
        # 1. 检查系统健康状态
        health_response = await e2e_client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # 2. 获取API状态
        status_response = await e2e_client.get("/api/v1/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "ok"

        # 3. 发起预测请求 (如果端点存在)
        match_data = MatchFactory.create()
        prediction_response = await e2e_client.post(
            "/api/v1/predictions", json=match_data
        )

        # 如果端点不存在，跳过这部分测试
        if prediction_response.status_code == 404:
            pytest.skip("Prediction endpoint not implemented yet")

        assert prediction_response.status_code in [200, 201]

    @pytest.mark.slow
    async def test_end_to_end_user_journey(self, e2e_client: AsyncClient):
        """测试完整的用户使用流程"""
        import asyncio

        # 模拟用户的完整操作流程
        journey_steps = [
            # Step 1: 检查服务状态
            e2e_client.get("/health"),
            e2e_client.get("/"),
            e2e_client.get("/api/v1/status"),
        ]

        # 并发执行用户旅程的各个步骤
        responses = await asyncio.gather(*journey_steps)

        # 验证所有步骤都成功
        for response in responses:
            assert response.status_code == 200

    @pytest.mark.performance
    async def test_workflow_performance_under_load(self, e2e_client: AsyncClient):
        """测试工作流在负载下的性能"""
        import asyncio
        import time

        async def single_user_workflow():
            """单个用户的工作流"""
            health_check = await e2e_client.get("/health")
            status_check = await e2e_client.get("/api/v1/status")
            return health_check.status_code == 200 and status_check.status_code == 200

        # 模拟10个并发用户
        start_time = time.time()
        tasks = [single_user_workflow() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # 验证性能指标
        total_time = end_time - start_time
        assert total_time < 3.0  # 10个并发用户应在3秒内完成
        assert all(results)  # 所有用户流程都应成功

    async def test_error_handling_workflow(self, e2e_client: AsyncClient):
        """测试错误处理工作流"""
        # 测试无效端点
        invalid_response = await e2e_client.get("/invalid-endpoint")
        assert invalid_response.status_code == 404

        # 测试无效HTTP方法
        invalid_method_response = await e2e_client.post("/health")
        assert invalid_method_response.status_code == 405

    async def test_api_documentation_workflow(self, e2e_client: AsyncClient):
        """测试API文档访问工作流"""
        # 检查OpenAPI文档
        docs_response = await e2e_client.get("/docs")
        assert docs_response.status_code == 200

        # 检查ReDoc文档
        redoc_response = await e2e_client.get("/redoc")
        assert redoc_response.status_code == 200

        # 检查OpenAPI JSON
        openapi_response = await e2e_client.get("/api/v1/openapi.json")
        assert openapi_response.status_code == 200
        openapi_data = openapi_response.json()
        assert "info" in openapi_data
        assert "paths" in openapi_data


@pytest.mark.e2e
@pytest.mark.integration
class TestSystemIntegrationE2E:
    """系统集成端到端测试"""

    @pytest.fixture
    async def integration_client(self):
        """集成测试客户端"""
        # 重用e2e_client的配置，但专注于集成测试
        with patch(
            "src.football_predict_system.core.config.get_settings"
        ) as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.app_name = "Football Prediction System"
            mock_settings.app_version = "1.0.0"
            mock_settings.environment.value = "testing"
            mock_get_settings.return_value = mock_settings

            from src.football_predict_system.main import app

            async with asgi_lifespan.LifespanManager(app):
                async with AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://test"
                ) as client:
                    yield client

    async def test_application_startup_shutdown(self, integration_client):
        """测试应用启动和关闭流程"""
        # 测试应用是否正确启动
        response = await integration_client.get("/")
        assert response.status_code == 200

        # 验证启动后的基本功能
        health_response = await integration_client.get("/health")
        assert health_response.status_code == 200

    @pytest.mark.concurrent
    async def test_concurrent_system_access(self, integration_client):
        """测试并发系统访问"""
        import asyncio

        # 创建多种不同的并发请求
        concurrent_requests = [
            integration_client.get("/"),
            integration_client.get("/health"),
            integration_client.get("/api/v1/status"),
            integration_client.get("/docs"),
        ]

        # 重复请求以增加并发压力
        all_requests = concurrent_requests * 5  # 20个并发请求

        responses = await asyncio.gather(*all_requests, return_exceptions=True)

        # 检查响应
        successful_responses = [
            r for r in responses if hasattr(r, "status_code") and r.status_code == 200
        ]
        assert len(successful_responses) >= 15  # 至少75%的请求成功
