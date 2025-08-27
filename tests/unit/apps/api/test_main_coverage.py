"""
API主模块的覆盖率测试
"""

from unittest.mock import patch

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

    @patch("apps.api.main.predictor")
    def test_predict_endpoint_coverage(self, mock_predictor, client):
        """测试预测端点覆盖率"""
        mock_predictor.predict_batch.return_value = [
            {
                "home_team": "Team A",
                "away_team": "Team B",
                "home_win": 0.45,
                "draw": 0.25,
                "away_win": 0.30,
                "predicted_outcome": "home_win",
                "confidence": 0.45,
                "model_version": "test-v1.0",
            }
        ]

        test_data = [
            {
                "home": "Team A",
                "away": "Team B",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.0,
                "odds_d": 3.2,
                "odds_a": 3.8,
            }
        ]

        response = client.post("/predict", json=test_data)
        assert response.status_code == 200

        predictions = response.json()
        assert len(predictions) == 1
        # The API response doesn't include team names, so we check for probability keys
        assert "home_win" in predictions[0]
        assert "draw" in predictions[0]
        assert "away_win" in predictions[0]

    def test_predict_endpoint_error_cases(self, client):
        """测试预测端点错误情况覆盖率"""
        # 测试空请求
        response = client.post("/predict", json=[])
        assert response.status_code == 400

        # 测试过大请求
        large_request = [
            {
                "home": f"Team{i}",
                "away": f"Team{i+1}",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.0,
                "odds_d": 3.0,
                "odds_a": 4.0,
            }
            for i in range(101)
        ]
        response = client.post("/predict", json=large_request)
        assert response.status_code == 400
