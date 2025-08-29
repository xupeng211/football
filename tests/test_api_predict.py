"""
FastAPI预测接口测试
"""

from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.prediction_service import prediction_service
from models.predictor import Predictor

# 确保预测服务在测试中被正确初始化
if prediction_service._predictor is None:
    predictor = Predictor()
    prediction_service.set_predictor(predictor)

client = TestClient(app)


def test_health_endpoint():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "components" in data


def test_version_endpoint():
    """测试版本信息接口"""
    response = client.get("/version")
    assert response.status_code == 200

    data = response.json()
    assert "api_version" in data
    assert "model_version" in data
    assert "model_info" in data


def test_predict_smoke(monkeypatch):
    """测试预测接口冒烟测试"""

    # Mock the prediction service
    monkeypatch.setattr(
        "apps.api.services.prediction_service.prediction_service",
        lambda: type(
            "MockPredictionService",
            (object,),
            {
                "predict_batch": lambda self, matches, model_name=None: [
                    {
                        "home_win": 0.4,
                        "draw": 0.3,
                        "away_win": 0.3,
                        "model_version": "test_v1",
                    }
                    for _ in matches
                ]
            },
        )(),
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

    assert response.status_code == 200

    data = response.json()
    assert len(data["predictions"]) == 1
    prediction = data["predictions"][0]
    assert "predicted_outcome" in prediction
    assert "confidence" in prediction


def test_predict_empty_list():
    """测试空列表预测请求"""
    response = client.post("/api/v1/predict/batch", json={"matches": []})
    assert response.status_code == 422


def test_predict_too_many_matches():
    """测试过多比赛请求"""
    matches = [
        {
            "home_team": f"Team{i}",
            "away_team": f"Team{i + 1}",
            "match_date": "2025-08-30",
            "home_odds": 2.0,
            "draw_odds": 3.0,
            "away_odds": 3.0,
        }
        for i in range(101)  # 超过100场
    ]

    response = client.post("/api/v1/predict/batch", json={"matches": matches})
    assert response.status_code == 200  # No max limit by default


def test_root_endpoint():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data


def test_predict_422():
    from fastapi.testclient import TestClient

    from apps.api.main import app

    # Send invalid data (empty match object)
    r = TestClient(app).post("/api/v1/predict/batch", json={"matches": [{}]})
    assert r.status_code == 422
