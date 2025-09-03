"""
FastAPI预测接口测试
"""

import pytest
from fastapi.testclient import TestClient

from football_predict_system.core.constants import HTTPStatus
from football_predict_system.main import app

# 跳过API预测测试用于CI(集成问题)
pytestmark = pytest.mark.skip_for_ci

# NOTE: 预测服务模块实现已延期到v2.0
# 当前测试使用模拟预测器进行基础功能验证
# 相关issue: https://github.com/project/issues/prediction-service

client = TestClient(app)


def test_health_endpoint():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "components" in data


def test_version_endpoint():
    """测试版本信息接口"""
    response = client.get("/version")
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert "api_version" in data
    assert "model_version" in data
    assert "model_info" in data


def test_predict_smoke(monkeypatch):
    """测试预测接口冒烟测试"""

    # Mock the prediction service's generate_batch_predictions method

    async def mock_generate_batch_predictions(self, request):
        from datetime import datetime
        from uuid import uuid4

        from football_predict_system.domain.models import (
            BatchPredictionResponse,
            MatchResult,
            Prediction,
            PredictionConfidence,
            PredictionResponse,
        )

        # Create a proper Prediction object
        prediction = Prediction(
            id=uuid4(),
            match_id=uuid4(),
            model_version="test_v1",
            predicted_result=MatchResult.HOME_WIN,
            home_win_probability=0.6,
            draw_probability=0.2,
            away_win_probability=0.2,
            confidence_level=PredictionConfidence.HIGH,
            confidence_score=0.75,
            created_at=datetime.utcnow(),
            prediction_date=datetime.utcnow(),
        )

        # Create proper PredictionResponse
        prediction_response = PredictionResponse(
            prediction=prediction,
            match_info={"home_team": "Arsenal", "away_team": "Chelsea"},
            model_info={"version": "test_v1", "accuracy": 0.85},
        )

        return BatchPredictionResponse(
            predictions=[prediction_response],
            total_count=1,
            successful_predictions=1,
            failed_predictions=0,
        )

    monkeypatch.setattr(
        "football_predict_system.domain.services.PredictionService.generate_batch_predictions",
        mock_generate_batch_predictions,
    )

    # Send a valid request to the correct endpoint
    response = client.post(
        "/api/v1/predict/batch",
        json={
            "matches": [
                {
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "match_date": "2025-08-30",
                    "home_odds": 2.1,
                    "draw_odds": 3.3,
                    "away_odds": 3.2,
                }
            ]
        },
    )

    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert len(data["predictions"]) == 1
    prediction = data["predictions"][0]
    assert "predicted_outcome" in prediction
    assert "confidence" in prediction


def test_predict_empty_list():
    """测试空列表预测请求"""
    response = client.post("/api/v1/predict/batch", json={"matches": []})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_predict_too_many_matches():
    """测试过多比赛请求"""
    matches = [
        {
            "home_team": f"Team{i}",
            "away_team": f"Team{i + 1}",
            "match_date": "2025-08-30",
            "home_odds": 2.0,
            "draw_odds": 3.0,
            "away_odds": 3.5,
        }
        for i in range(101)  # 超过最大100场比赛限制
    ]

    response = client.post("/api/v1/predict/batch", json={"matches": matches})
    # 应该期望422状态码, 因为超过了最大比赛数量限制
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_root_endpoint():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK

    data = response.json()
    assert "message" in data


def test_predict_422():
    from fastapi.testclient import TestClient

    from football_predict_system.api.main import app

    # Send invalid data (empty match object)
    r = TestClient(app).post("/api/v1/predict/batch", json={"matches": [{}]})
    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
