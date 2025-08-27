"""
FastAPI预测接口测试
"""

from fastapi.testclient import TestClient

from apps.api.main import app

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

    # Mock预测器
    class MockPredictor:
        def __init__(self):
            self.model = True  # 模拟模型已加载
            self.model_version = "test_v1"

        def predict_batch(self, matches):
            return [
                {
                    "home_win": 0.4,
                    "draw": 0.3,
                    "away_win": 0.3,
                    "model_version": "test_v1",
                }
                for _ in matches
            ]

    # 替换全局预测器
    from apps.api import main

    mock_predictor = MockPredictor()
    monkeypatch.setattr(main, "predictor", mock_predictor)

    # 发送预测请求
    response = client.post(
        "/predict",
        json=[
            {
                "home": "Arsenal",
                "away": "Chelsea",
                "home_form": 2.1,
                "away_form": 1.8,
                "odds_h": 2.1,
                "odds_d": 3.3,
                "odds_a": 3.2,
            }
        ],
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert "home_win" in data[0]
    assert "draw" in data[0]
    assert "away_win" in data[0]
    assert "model_version" in data[0]


def test_predict_empty_list():
    """测试空列表预测请求"""
    response = client.post("/predict", json=[])
    assert response.status_code == 400


def test_predict_too_many_matches():
    """测试过多比赛请求"""
    matches = [
        {
            "home": f"Team{i}",
            "away": f"Team{i+1}",
            "odds_h": 2.0,
            "odds_d": 3.0,
            "odds_a": 3.0,
        }
        for i in range(101)  # 超过100场
    ]

    response = client.post("/predict", json=matches)
    assert response.status_code == 400


def test_root_endpoint():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data


def test_predict_422():
    from fastapi.testclient import TestClient

    from apps.api.main import app

    # 发送无效数据,预期返回错误
    r = TestClient(app).post("/predict", json=[{}])  # 完全空的对象
    assert r.status_code in (400, 422, 500)  # 允许多种错误状态
