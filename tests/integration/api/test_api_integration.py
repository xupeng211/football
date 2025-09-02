"""
API集成测试
测试完整的API工作流程和模块间交互
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from football_predict_system.main import app


class TestAPIIntegration:
    """API集成测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    def test_api_startup_flow(self, client):
        """测试API启动流程"""
        # 健康检查应该总是可用
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "message" in data

    def test_version_endpoint_integration(self, client):
        """测试版本信息接口的集成功能"""
        response = client.get("/version")
        assert response.status_code == 200

        data = response.json()
        assert "api_version" in data
        assert "model_version" in data
        assert data["api_version"] == "1.0.0"

    def test_root_endpoint_integration(self, client):
        """测试根路径接口"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert data["docs"] == "/docs"

    @patch("apps.api.main.predictor")
    def test_prediction_endpoint_integration(self, mock_predictor, client):
        """测试预测接口的完整集成流程"""
        # 设置mock预测器
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

        # 准备测试数据
        test_matches = [
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

        # 发送预测请求
        response = client.post("/predict", json=test_matches)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1

        prediction = data[0]
        # API response no longer contains team names, so these assertions are removed.
        assert "confidence" in prediction
        assert "home_win" in prediction
        assert "predicted_outcome" in prediction

    def test_prediction_empty_input(self, client):
        """测试空输入的预测请求"""
        response = client.post("/predict", json=[])
        assert response.status_code == 400
        assert "不能为空" in response.json()["detail"]

    def test_prediction_too_many_matches(self, client):
        """测试超出限制的批量预测"""
        # 创建超过100场比赛的请求
        large_request = [
            {
                "home": f"Team A{i}",
                "away": f"Team B{i}",
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
        assert "最多支持100场比赛" in response.json()["detail"]

    def test_prediction_invalid_input_format(self, client):
        """测试无效输入格式"""
        # 缺少必需字段 "away"
        invalid_request = [
            {
                "home": "Team A",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.0,
                "odds_d": 3.2,
                "odds_a": 3.8,
            }
        ]
        response = client.post("/predict", json=invalid_request)
        assert response.status_code == 422  # Validation error

    @patch("apps.api.main.predictor")
    def test_prediction_with_predictor_error(self, mock_predictor, client):
        """测试预测器出错时的处理"""
        # 模拟预测器抛出异常
        mock_predictor.predict_batch.side_effect = Exception("Model error")

        test_matches = [
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

        response = client.post("/predict", json=test_matches)
        assert response.status_code == 500
        assert "预测失败" in response.json()["detail"]

    def test_api_cors_headers(self, client):
        """测试CORS头部设置"""
        response = client.options("/predict")
        # 根据实际CORS配置验证头部
        assert response.status_code in [200, 405]  # OPTIONS可能不被允许

    def test_api_error_handling_flow(self, client):
        """测试API错误处理流程"""
        # 测试不存在的端点
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # 测试不支持的方法
        response = client.patch("/health")
        assert response.status_code == 405


class TestAPIDataFlow:
    """API数据流集成测试"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @patch("apps.api.main.predictor")
    def test_complete_prediction_workflow(self, mock_predictor, client):
        """测试完整的预测工作流程"""
        # 步骤1: 检查服务状态
        health_response = client.get("/health")
        assert health_response.status_code == 200

        # 步骤2: 获取版本信息
        mock_predictor.model_version = "test-v1.0"
        mock_predictor.get_model_info.return_value = {"info": "mocked_model"}
        version_response = client.get("/version")
        assert version_response.status_code == 200

        # 步骤3: 准备预测数据
        mock_predictor.predict_batch.return_value = [
            {
                "home_win": 0.40,
                "draw": 0.30,
                "away_win": 0.30,
                "predicted_outcome": "home_win",
                "confidence": 0.40,
                "model_version": "v1.0",
            },
            {
                "home_win": 0.35,
                "draw": 0.35,
                "away_win": 0.30,
                "predicted_outcome": "draw",
                "confidence": 0.35,
                "model_version": "v1.0",
            },
        ]

        # 步骤4: 执行批量预测
        matches = [
            {
                "home": "Manchester United",
                "away": "Liverpool",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.5,
                "odds_d": 3.2,
                "odds_a": 3.0,
            },
            {
                "home": "Chelsea",
                "away": "Arsenal",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.8,
                "odds_d": 3.0,
                "odds_a": 2.9,
            },
        ]

        prediction_response = client.post("/predict", json=matches)
        assert prediction_response.status_code == 200

        # 验证返回数据
        predictions = prediction_response.json()
        assert len(predictions) == 2

        # 验证第一场比赛预测
        first_prediction = predictions[0]
        assert first_prediction["predicted_outcome"] == "home_win"

        # 验证第二场比赛预测
        second_prediction = predictions[1]
        assert second_prediction["predicted_outcome"] == "draw"

        # 验证所有预测都有必需字段
        required_fields = [
            "home_win",
            "draw",
            "away_win",
            "predicted_outcome",
            "confidence",
        ]
        for prediction in predictions:
            for field in required_fields:
                assert field in prediction


class TestAPIPerformance:
    """API性能集成测试"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @patch("apps.api.main.predictor")
    def test_api_response_time(self, mock_predictor, client):
        """测试API响应时间"""
        import time

        # 设置快速响应的mock
        mock_predictor.predict_batch.return_value = [
            {
                "home_team": "A",
                "away_team": "B",
                "home_win": 0.5,
                "draw": 0.3,
                "away_win": 0.2,
                "predicted_outcome": "home_win",
                "confidence": 0.5,
                "model_version": "v1.0",
            }
        ]

        # 测量响应时间
        start_time = time.time()

        response = client.post(
            "/predict",
            json=[
                {
                    "home": "Team A",
                    "away": "Team B",
                    "home_form": 1.5,
                    "away_form": 1.5,
                    "odds_h": 2.0,
                    "odds_d": 3.0,
                    "odds_a": 4.0,
                }
            ],
        )

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # 响应时间应该小于1秒

    @patch("apps.api.main.predictor")
    def test_concurrent_requests(self, mock_predictor, client):
        """测试并发请求处理"""
        import queue
        import threading

        mock_predictor.predict_batch.return_value = [
            {
                "home_team": "A",
                "away_team": "B",
                "home_win": 0.5,
                "draw": 0.3,
                "away_win": 0.2,
                "predicted_outcome": "home_win",
                "confidence": 0.5,
                "model_version": "v1.0",
            }
        ]

        results_queue = queue.Queue()

        def make_request():
            response = client.post(
                "/predict",
                json=[
                    {
                        "home": "Team A",
                        "away": "Team B",
                        "home_form": 1.5,
                        "away_form": 1.5,
                        "odds_h": 2.0,
                        "odds_d": 3.0,
                        "odds_a": 4.0,
                    }
                ],
            )
            results_queue.put(response.status_code)

        # 创建多个并发请求
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # 等待所有请求完成
        for thread in threads:
            thread.join()

        # 验证所有请求都成功
        while not results_queue.empty():
            status_code = results_queue.get()
            assert status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
