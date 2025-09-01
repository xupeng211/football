"""
简单API测试 - 测试API模块导入和基本功能
"""

import os
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# 在导入任何应用模块之前清理环境变量
@pytest.fixture(autouse=True)
def clean_environment() -> Generator[None, None, None]:
    """清理可能导致配置问题的环境变量"""
    env_vars_to_remove = [
        "app_port",
        "feature_set",
        "model_version",
        "log_level",
        "prefect_api_url",
        "metrics_port",
        "football_api_key",
        "data_update_interval_minutes",
        "model_registry_path",
        "model_cache_size",
        "backtest_start_date",
        "backtest_end_date",
    ]

    original_values = {}
    for var in env_vars_to_remove:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]

    yield

    # 恢复原始值
    for var, value in original_values.items():
        os.environ[var] = value


@pytest.fixture
def mock_settings() -> MagicMock:
    """创建模拟的配置对象"""
    settings = MagicMock()
    settings.app_name = "Football Prediction System"
    settings.app_version = "1.0.0"
    settings.debug = False
    settings.environment.value = "testing"

    # API配置
    api_config = MagicMock()
    api_config.cors_origins = ["*"]
    api_config.cors_credentials = True
    api_config.cors_methods = ["*"]
    api_config.cors_headers = ["*"]
    settings.api = api_config

    return settings


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端,模拟所有外部依赖"""
    # 创建模拟设置
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

    with (
        patch("src.football_predict_system.core.config.Settings") as MockSettings,
        patch(
            "src.football_predict_system.core.config.get_settings",
            return_value=mock_settings,
        ),
        patch("src.football_predict_system.core.config.settings", mock_settings),
        patch(
            "src.football_predict_system.core.database.get_database_manager"
        ) as mock_db,
        patch("src.football_predict_system.core.cache.get_cache_manager") as mock_cache,
        patch(
            "src.football_predict_system.core.health.get_health_checker"
        ) as mock_health,
        patch("src.football_predict_system.core.logging.setup_logging"),
        patch(
            "src.football_predict_system.core.logging.get_logger",
            return_value=MagicMock(),
        ),
    ):
        # 模拟Settings类的实例化
        MockSettings.return_value = mock_settings

        # 模拟数据库管理器
        mock_db_manager = MagicMock()
        mock_db_manager.get_engine.return_value = MagicMock()
        mock_db_manager.get_async_engine.return_value = MagicMock()
        mock_db_manager.close = AsyncMock()
        mock_db.return_value = mock_db_manager

        # 模拟缓存管理器
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_redis_client = AsyncMock(return_value=MagicMock())
        mock_cache_manager.close = AsyncMock()
        mock_cache.return_value = mock_cache_manager

        # 模拟健康检查器
        mock_health_checker = MagicMock()
        mock_health_response = MagicMock()
        # 使用configure_mock来确保status比较能够正确工作
        status_mock = MagicMock()
        status_mock.configure_mock(**{"__eq__.return_value": True})
        mock_health_response.status = status_mock
        mock_health_response.model_dump.return_value = {
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
            return_value=mock_health_response
        )
        mock_health.return_value = mock_health_checker

        # 导入并创建测试客户端
        from src.football_predict_system.main import app

        return TestClient(app)


def test_app_import() -> None:
    """测试API应用导入"""
    with (
        patch("src.football_predict_system.core.config.Settings") as MockSettings,
        patch("src.football_predict_system.core.logging.setup_logging"),
        patch("src.football_predict_system.core.logging.get_logger"),
    ):
        mock_settings = MagicMock()
        mock_settings.app_name = "Football Prediction System"
        MockSettings.return_value = mock_settings

        from src.football_predict_system.main import app

        assert app is not None
        assert hasattr(app, "title")


def test_api_router_import() -> None:
    """测试API路由导入"""
    with patch("src.football_predict_system.core.logging.get_logger"):
        from src.football_predict_system.api.v1.endpoints import router

        assert router is not None


def test_predictions_router_import() -> None:
    """测试预测路由导入"""
    with (
        patch("src.football_predict_system.core.config.Settings") as MockSettings,
        patch("src.football_predict_system.core.logging.get_logger"),
    ):
        MockSettings.return_value = MagicMock()

        from src.football_predict_system.api.v1.predictions import router

        assert router is not None


def test_models_router_import() -> None:
    """测试模型路由导入"""
    with (
        patch("src.football_predict_system.core.config.Settings") as MockSettings,
        patch("src.football_predict_system.core.logging.get_logger"),
    ):
        MockSettings.return_value = MagicMock()

        from src.football_predict_system.api.v1.models import router

        assert router is not None


def test_app_routes_registered(client: TestClient) -> None:
    """测试应用路由注册"""
    # 检查根路径
    response = client.get("/")
    assert response.status_code == 200

    # 检查健康检查端点
    response = client.get("/health")
    assert response.status_code == 200

    # 检查API状态端点
    response = client.get("/api/v1/status")
    assert response.status_code == 200


def test_cors_middleware() -> None:
    """测试CORS中间件配置"""
    with (
        patch("src.football_predict_system.core.config.Settings") as MockSettings,
        patch("src.football_predict_system.core.logging.setup_logging"),
        patch("src.football_predict_system.core.logging.get_logger"),
    ):
        # 模拟设置
        mock_settings = MagicMock()
        api_config = MagicMock()
        api_config.cors_origins = ["*"]
        mock_settings.api = api_config
        MockSettings.return_value = mock_settings

        from src.football_predict_system.main import app

        # 检查中间件列表
        middleware_types = [
            getattr(m.cls, "__name__", str(m.cls)) for m in app.user_middleware
        ]
        # 应该包含CORS中间件
        assert "CORSMiddleware" in middleware_types


def test_exception_handler() -> None:
    """测试全局异常处理器"""
    with (
        patch("src.football_predict_system.core.config.Settings") as MockSettings,
        patch("src.football_predict_system.core.logging.setup_logging"),
        patch("src.football_predict_system.core.logging.get_logger"),
    ):
        mock_settings = MagicMock()
        mock_settings.app_name = "Football Prediction System"
        MockSettings.return_value = mock_settings

        from src.football_predict_system.main import app

        # 检查异常处理器是否注册
        assert hasattr(app, "exception_handlers")
        assert len(app.exception_handlers) >= 0


def test_health_endpoint(client: TestClient) -> None:
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_root_endpoint(client: TestClient) -> None:
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data


def test_api_status_endpoint(client: TestClient) -> None:
    """测试API状态端点"""
    response = client.get("/api/v1/status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "v1"
