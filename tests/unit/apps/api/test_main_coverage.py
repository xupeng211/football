"""
API主模块的覆盖率测试
"""

from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


class TestAPIMainCoverage:
    """API主模块覆盖率测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_api_app_creation(self):
        """测试API应用创建"""
        assert app is not None
        assert app.title == "足球预测API"

    def test_health_endpoint_coverage(self, client):
        """测试健康检查端点覆盖率"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "version" in data

    def test_version_endpoint_coverage(self, client):
        """测试版本端点覆盖率"""
        response = client.get("/version")
        assert response.status_code == 200

        data = response.json()
        assert "api_version" in data
        assert data["api_version"] == "1.0.0"

    def test_root_endpoint_coverage(self, client):
        """测试根端点覆盖率"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "docs" in data

    @patch("apps.api.services.prediction_service.prediction_service.predict")
    def test_predict_endpoint_coverage(self, mock_predict, client):
        """测试预测端点覆盖率"""
        mock_predict.return_value = np.array([[0.1, 0.2, 0.7]])
        response = client.post(
            "/api/v1/predict/single",
            json={
                "home_team": "A",
                "away_team": "B",
                "match_date": "2025-01-01",
                "home_odds": 2.0,
                "draw_odds": 3.0,
                "away_odds": 4.0,
            },
        )
        assert response.status_code == 200
        assert "prediction_id" in response.json()

    def test_predict_endpoint_error_cases(self, client):
        """测试预测端点错误情况覆盖率"""
        # Test with missing fields
        response = client.post("/api/v1/predict/single", json={"home_team": "A"})
        assert response.status_code == 422
