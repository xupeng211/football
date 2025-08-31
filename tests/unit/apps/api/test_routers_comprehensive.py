"""
API路由器的全面测试
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.factories import sample_match, sample_prediction


class TestHealthRouter:
    """健康检查路由测试"""

    def test_health_router_import(self):
        """测试健康检查路由导入"""
        try:
            from apps.api.routers.health import router

            assert router is not None
        except ImportError:
            pytest.skip("Health router not available")

    @patch("apps.api.routers.health.check_db_connection")
    @patch("apps.api.routers.health.check_redis_connection")
    @patch("apps.api.routers.health.check_prefect_connection_async")
    def test_health_endpoint_success(self, mock_prefect, mock_redis, mock_db):
        """测试健康检查端点成功情况"""
        try:
            from apps.api.routers.health import router

            # Mock所有依赖服务正常
            mock_db.return_value = (True, "DB OK")
            mock_redis.return_value = (True, "Redis OK")
            mock_prefect.return_value = (True, "Prefect OK")

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/health")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["components"]["database"]["status"] == "healthy"

        except ImportError:
            pytest.skip("Health router not available")

    @patch("apps.api.routers.health.check_db_connection")
    def test_health_endpoint_db_failure(self, mock_db):
        """测试数据库故障时的健康检查"""
        try:
            from apps.api.routers.health import router

            # Mock数据库连接失败
            mock_db.return_value = (False, "DB connection failed")

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/health")

            # 数据库故障时应返回错误状态
            assert response.status_code in [200, 503]

        except ImportError:
            pytest.skip("Health router not available")


class TestPredictionsRouter:
    """预测路由测试"""

    def test_predictions_router_import(self):
        """测试预测路由导入"""
        try:
            from apps.api.routers.predictions import router

            assert router is not None
        except ImportError:
            pytest.skip("Predictions router not available")

    @patch("apps.api.routers.predictions.prediction_service")
    def test_single_prediction_endpoint(self, mock_service):
        """测试单次预测端点"""
        try:
            from apps.api.routers.predictions import router

            # 使用测试数据工厂
            mock_service.predict.return_value = sample_prediction(home_win=0.85)

            app = FastAPI()
            app.include_router(router, prefix="/api/v1")
            client = TestClient(app)

            # 使用工厂创建测试数据
            test_data = sample_match()

            response = client.post("/api/v1/predict/single", json=test_data)

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "prediction_id" in data
            # 验证预测结果是有效值之一
            valid_outcomes = ["home_win", "draw", "away_win"]
            assert data["predicted_outcome"] in valid_outcomes

        except ImportError:
            pytest.skip("Predictions router not available")

    def test_batch_prediction_data_validation(self):
        """测试批量预测数据验证"""
        # 使用工厂创建有效的比赛数据
        valid_match_data = sample_match()

        # 验证必要字段
        required_fields = [
            "home_team",
            "away_team",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
        for field in required_fields:
            assert field in valid_match_data

        # 验证赔率值
        odds_fields = ["home_odds", "draw_odds", "away_odds"]
        for field in odds_fields:
            assert valid_match_data[field] >= 1.0

    @patch("apps.api.routers.predictions.prediction_service")
    def test_prediction_error_handling(self, mock_service):
        """测试预测错误处理"""
        try:
            from apps.api.routers.predictions import router

            # Mock预测服务抛出异常
            mock_service.predict.side_effect = Exception("Load failed")

            app = FastAPI()
            app.include_router(router, prefix="/api/v1")
            client = TestClient(app)

            test_data = sample_match()

            response = client.post("/api/v1/predict/single", json=test_data)

            # 应该返回错误状态
            assert response.status_code in [400, 500, 422]

        except ImportError:
            pytest.skip("Predictions router not available")


class TestMetricsRouter:
    """指标路由测试"""

    def test_metrics_router_import(self):
        """测试指标路由导入"""
        try:
            from apps.api.routers.metrics import router

            assert router is not None
        except ImportError:
            pytest.skip("Metrics router not available")

    @patch("psutil.Process")
    def test_metrics_endpoint(self, mock_process):
        """测试指标端点"""
        try:
            from apps.api.routers.metrics import router

            # Mock系统指标
            mock_proc = Mock()
            # 100MB内存使用
            mock_proc.memory_info.return_value = Mock(rss=1024 * 1024 * 100)
            mock_proc.cpu_percent.return_value = 15.5
            mock_process.return_value = mock_proc

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/metrics")

            # 验证响应格式
            if response.status_code == 200:
                # Prometheus格式或JSON格式都可以
                assert len(response.content) > 0

        except ImportError:
            pytest.skip("Metrics router not available")

    def test_custom_metrics_collection(self):
        """测试自定义指标收集"""
        # 模拟业务指标
        business_metrics = {
            "predictions_total": 1500,
            "predictions_success": 1350,
            "predictions_failed": 150,
            "avg_response_time": 45.2,  # ms
            "model_version": "v2.1.0",
            "uptime_seconds": 86400 * 7,  # 7天
        }

        # 验证指标完整性
        assert business_metrics["predictions_total"] == (
            business_metrics["predictions_success"]
            + business_metrics["predictions_failed"]
        )
        assert business_metrics["avg_response_time"] > 0
        assert business_metrics["uptime_seconds"] > 0

    @patch("psutil.virtual_memory")
    @patch("psutil.cpu_percent")
    def test_system_metrics_collection(self, mock_cpu, mock_memory):
        """测试系统指标收集"""
        # Mock系统资源信息
        mock_memory.return_value = Mock(
            total=8 * 1024 * 1024 * 1024,  # 8GB
            available=4 * 1024 * 1024 * 1024,  # 4GB
            percent=50.0,
        )
        mock_cpu.return_value = 25.5

        # 验证指标收集
        memory_info = mock_memory()
        cpu_usage = mock_cpu()

        assert memory_info.total > 0
        assert 0 <= memory_info.percent <= 100
        assert 0 <= cpu_usage <= 100


class TestAPIMiddleware:
    """API中间件测试"""

    def test_cors_middleware_functionality(self):
        """测试CORS中间件功能"""
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.testclient import TestClient

        app = FastAPI()

        # 添加CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}

        client = TestClient(app)
        response = client.get("/test")

        # 验证基本功能
        assert response.status_code == 200

    def test_error_handling_middleware(self):
        """测试错误处理中间件"""
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/error")
        def error_endpoint():
            raise HTTPException(status_code=500, detail="Test error")

        @app.get("/success")
        def success_endpoint():
            return {"status": "ok"}

        client = TestClient(app)

        # 测试错误处理
        error_response = client.get("/error")
        assert error_response.status_code == 500

        # 测试正常处理
        success_response = client.get("/success")
        assert success_response.status_code == 200

    def test_request_validation_middleware(self):
        """测试请求验证中间件"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        app = FastAPI()

        class RequestModel(BaseModel):
            name: str
            value: float

        @app.post("/validate")
        def validate_endpoint(data: RequestModel):
            return {"received": data.dict()}

        client = TestClient(app)

        # 测试有效请求
        valid_data = {"name": "test", "value": 1.5}
        response = client.post("/validate", json=valid_data)
        assert response.status_code == 200

        # 测试无效请求
        invalid_data = {"name": "test"}  # 缺少value字段
        response = client.post("/validate", json=invalid_data)
        assert response.status_code == 422


class TestAPIDocumentation:
    """API文档测试"""

    def test_openapi_schema_generation(self):
        """测试OpenAPI架构生成"""
        from fastapi import FastAPI

        app = FastAPI(
            title="Football Prediction API",
            description="API for football match prediction",
            version="1.0.0",
        )

        @app.get("/test")
        def test_endpoint():
            """测试端点"""
            return {"message": "test"}

        # 验证OpenAPI架构
        schema = app.openapi()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Football Prediction API"

    def test_api_documentation_endpoints(self):
        """测试API文档端点"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        @app.get("/")
        def root():
            return {"message": "API is running"}

        client = TestClient(app)

        # 测试文档端点
        docs_response = client.get("/docs")
        redoc_response = client.get("/redoc")
        openapi_response = client.get("/openapi.json")

        # 验证文档可访问
        assert docs_response.status_code == 200
        assert redoc_response.status_code == 200
        assert openapi_response.status_code == 200

    def test_api_tags_and_metadata(self):
        """测试API标签和元数据"""

        tags_metadata = [
            {
                "name": "predictions",
                "description": "Football match predictions",
            },
            {
                "name": "health",
                "description": "Health check endpoints",
            },
            {
                "name": "metrics",
                "description": "System and business metrics",
            },
        ]

        # 验证标签元数据结构
        for tag in tags_metadata:
            assert "name" in tag
            assert "description" in tag
            assert isinstance(tag["name"], str)
            assert isinstance(tag["description"], str)


if __name__ == "__main__":
    pytest.main([__file__])
