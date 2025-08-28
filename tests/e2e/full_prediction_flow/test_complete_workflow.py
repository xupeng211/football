"""
端到端测试 - 完整的用户工作流程
测试从数据输入到最终预测结果的完整流程
"""

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


class TestCompleteUserWorkflow:
    """完整用户工作流程的端到端测试"""

    @pytest.fixture
    def api_client(self):
        """创建API测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def sample_user_data(self):
        """模拟真实用户输入数据"""
        return [
            {
                "home": "Manchester United",
                "away": "Liverpool",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.50,
                "odds_d": 3.20,
                "odds_a": 3.00,
            },
            {
                "home": "Chelsea",
                "away": "Arsenal",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.80,
                "odds_d": 3.10,
                "odds_a": 2.70,
            },
            {
                "home": "Manchester City",
                "away": "Tottenham",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 1.90,
                "odds_d": 3.80,
                "odds_a": 4.20,
            },
        ]

    def test_complete_prediction_workflow(self, api_client, sample_user_data):
        """测试完整的预测工作流程"""
        # 步骤1: 用户检查系统状态
        print("📝 步骤1: 检查系统健康状态")
        health_response = api_client.get("/health")
        assert health_response.status_code == 200

        health_data = health_response.json()
        print(f"✅ 系统状态: {health_data['status']}")

        # 步骤2: 用户获取API版本信息
        print("\n📝 步骤2: 获取API版本信息")
        version_response = api_client.get("/version")
        assert version_response.status_code == 200

        version_data = version_response.json()
        print(f"✅ API版本: {version_data['api_version']}")
        print(f"✅ 模型版本: {version_data.get('model_version', 'unknown')}")

        # 步骤3: 用户提交预测请求
        print("\n📝 步骤3: 提交批量预测请求")
        print(f"🎯 预测 {len(sample_user_data)} 场比赛")

        prediction_response = api_client.post("/predict", json=sample_user_data)
        assert prediction_response.status_code == 200

        predictions = prediction_response.json()
        assert len(predictions) == len(sample_user_data)

        # 步骤4: 用户验证预测结果
        print("\n📝 步骤4: 验证预测结果")
        for i, prediction in enumerate(predictions):
            match_data = sample_user_data[i]
            print(f"\n🏈 比赛 {i + 1}: {match_data['home']} vs {match_data['away']}")
            print(f"   预测结果: {prediction['predicted_outcome']}")
            print(f"   主胜概率: {prediction['home_win']:.2%}")
            print(f"   平局概率: {prediction['draw']:.2%}")
            print(f"   客胜概率: {prediction['away_win']:.2%}")
            print(f"   预测置信度: {prediction['confidence']:.2%}")

            # 验证预测数据完整性
            required_fields = [
                "home_win",
                "draw",
                "away_win",
                "predicted_outcome",
                "confidence",
            ]
            for field in required_fields:
                assert field in prediction, f"Missing field: {field}"

            # 验证概率值合理性
            total_prob = (
                prediction["home_win"] + prediction["draw"] + prediction["away_win"]
            )
            assert (
                abs(total_prob - 1.0) < 0.01
            ), f"Probabilities don't sum to 1: {total_prob}"

            # 验证置信度范围
            assert (
                0 <= prediction["confidence"] <= 1
            ), f"Invalid confidence: {prediction['confidence']}"

        print("\n✅ 完整工作流程测试通过!")

    def test_user_error_handling_workflow(self, api_client):
        """测试用户错误处理工作流程"""
        print("📝 测试用户错误处理场景")

        # 场景1: 用户提交空请求
        print("\n🚫 场景1: 空预测请求")
        empty_response = api_client.post("/predict", json=[])
        assert empty_response.status_code == 400
        print("✅ 正确拒绝空请求")

        # 场景2: 用户提交格式错误的数据
        print("\n🚫 场景2: 格式错误的数据")
        invalid_data = [{"home": "Team A"}]  # 缺少必需字段
        invalid_response = api_client.post("/predict", json=invalid_data)
        assert invalid_response.status_code == 422
        print("✅ 正确拒绝无效格式")

        # 场景3: 用户提交过多数据
        print("\n🚫 场景3: 超出限制的批量请求")
        large_data = [
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
        large_response = api_client.post("/predict", json=large_data)
        assert large_response.status_code == 400
        print("✅ 正确拒绝超大批量")

        print("\n✅ 错误处理工作流程测试通过!")

    @patch("apps.api.main.predictor")
    def test_user_real_world_scenarios(self, mock_predictor, api_client):
        """测试真实世界使用场景"""
        print("📝 测试真实世界使用场景")

        # 设置真实的预测响应
        mock_predictor.predict_batch.return_value = [
            {
                "home_team": "Real Madrid",
                "away_team": "Barcelona",
                "home_win": 0.45,
                "draw": 0.25,
                "away_win": 0.30,
                "predicted_outcome": "home_win",
                "confidence": 0.45,
                "model_version": "v1.0",
            }
        ]

        # 场景1: 经典德比大战预测
        print("\n🏆 场景1: 经典德比大战")
        classico = [
            {
                "home": "Real Madrid",
                "away": "Barcelona",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.30,
                "odds_d": 3.50,
                "odds_a": 3.20,
            }
        ]

        response = api_client.post("/predict", json=classico)
        assert response.status_code == 200

        result = response.json()[0]
        print(f"   预测: {result['predicted_outcome']}")
        print(f"   置信度: {result['confidence']:.2%}")
        print("✅ 德比预测成功")

        # 场景2: 多场同时预测(周末赛程)
        print("\n📅 场景2: 周末多场比赛预测")
        weekend_matches = [
            {
                "home": f"Home{i}",
                "away": f"Away{i}",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.0 + i * 0.1,
                "odds_d": 3.0,
                "odds_a": 4.0 - i * 0.1,
            }
            for i in range(10)
        ]

        # 模拟批量响应
        mock_predictor.predict_batch.return_value = [
            {
                "home_team": f"Home{i}",
                "away_team": f"Away{i}",
                "home_win": 0.4 + i * 0.01,
                "draw": 0.3,
                "away_win": 0.3 - i * 0.01,
                "predicted_outcome": "home_win",
                "confidence": 0.4 + i * 0.01,
                "model_version": "v1.0",
            }
            for i in range(10)
        ]

        response = api_client.post("/predict", json=weekend_matches)
        assert response.status_code == 200

        results = response.json()
        assert len(results) == 10
        print(f"✅ 成功预测 {len(results)} 场周末比赛")

        print("\n✅ 真实世界场景测试通过!")

    def test_user_performance_expectations(self, api_client):
        """测试用户性能期望"""
        print("📝 测试用户性能期望")

        # 单次预测响应时间测试
        print("\n⏱️ 测试单次预测响应时间")
        single_match = [
            {
                "home": "Performance Test A",
                "away": "Performance Test B",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.0,
                "odds_d": 3.0,
                "odds_a": 4.0,
            }
        ]

        start_time = time.time()
        response = api_client.post("/predict", json=single_match)
        end_time = time.time()

        response_time = end_time - start_time
        print(f"   响应时间: {response_time:.3f} 秒")

        assert response.status_code == 200
        assert response_time < 2.0, f"响应时间 {response_time:.3f}s 超过用户期望"
        print("✅ 响应时间满足用户期望")

        # 批量预测性能测试
        print("\n📊 测试批量预测性能")
        batch_sizes = [5, 10, 20, 50]

        for batch_size in batch_sizes:
            batch_matches = [
                {
                    "home": f"Batch{i}A",
                    "away": f"Batch{i}B",
                    "home_form": 1.5,
                    "away_form": 1.5,
                    "odds_h": 2.0,
                    "odds_d": 3.0,
                    "odds_a": 4.0,
                }
                for i in range(batch_size)
            ]

            start_time = time.time()
            response = api_client.post("/predict", json=batch_matches)
            end_time = time.time()

            response_time = end_time - start_time
            time_per_prediction = response_time / batch_size

            print(
                f"   批量大小 {batch_size}: {response_time:.3f}s 总时间, {time_per_prediction:.3f}s/预测"
            )

            assert response.status_code == 200
            assert len(response.json()) == batch_size

        print("✅ 批量预测性能满足要求")


class TestUserDataIntegration:
    """用户数据集成测试"""

    @pytest.fixture
    def api_client(self):
        return TestClient(app)

    def test_data_format_compatibility(self, api_client):
        """测试数据格式兼容性"""
        print("📝 测试数据格式兼容性")

        # 测试不同的有效数据格式
        format_variations = [
            # 标准格式
            {
                "home": "Standard Home",
                "away": "Standard Away",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.50,
                "odds_d": 3.20,
                "odds_a": 3.00,
            },
            # 整数赔率
            {
                "home": "Integer Home",
                "away": "Integer Away",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2,
                "odds_d": 3,
                "odds_a": 4,
            },
            # 高精度赔率
            {
                "home": "Precise Home",
                "away": "Precise Away",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.547,
                "odds_d": 3.198,
                "odds_a": 2.999,
            },
        ]

        for i, format_test in enumerate(format_variations):
            print(f"\n🔄 测试格式变体 {i + 1}")
            response = api_client.post("/predict", json=[format_test])

            assert response.status_code == 200, f"Format variation {i + 1} failed"

            result = response.json()[0]
            assert "predicted_outcome" in result
            print(f"✅ 格式变体 {i + 1} 通过")

        print("\n✅ 所有数据格式兼容性测试通过!")

    def test_edge_case_data_handling(self, api_client):
        """测试边界情况数据处理"""
        print("📝 测试边界情况数据处理")

        edge_cases = [
            # 极端赔率
            {
                "home": "Extreme Favorite",
                "away": "Extreme Underdog",
                "home_form": 3.0,
                "away_form": 0.5,
                "odds_h": 1.01,
                "odds_d": 15.0,
                "odds_a": 50.0,
            },
            # 非常接近的赔率
            {
                "home": "Close Match A",
                "away": "Close Match B",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.001,
                "odds_d": 2.002,
                "odds_a": 2.003,
            },
            # 特殊队名
            {
                "home": "FC Barcelona & Real Madrid United",
                "away": "Manchester City F.C. (England)",
                "home_form": 1.5,
                "away_form": 1.5,
                "odds_h": 2.5,
                "odds_d": 3.2,
                "odds_a": 3.0,
            },
        ]

        for i, edge_case in enumerate(edge_cases):
            print(f"\n🚨 测试边界情况 {i + 1}")
            response = api_client.post("/predict", json=[edge_case])

            # 边界情况应该被优雅处理,不应该导致服务器错误
            assert response.status_code in [
                200,
                400,
                422,
            ], f"Edge case {i + 1} caused server error: {response.status_code}"

            if response.status_code == 200:
                result = response.json()[0]
                assert "predicted_outcome" in result
                print(f"✅ 边界情况 {i + 1} 成功处理")
            else:
                print(f"⚠️ 边界情况 {i + 1} 被正确拒绝")

        print("\n✅ 边界情况处理测试通过!")


class TestEndToEndMonitoring:
    """端到端监控测试"""

    @pytest.fixture
    def api_client(self):
        return TestClient(app)

    def test_system_health_monitoring(self, api_client):
        """测试系统健康监控"""
        print("📝 测试系统健康监控")

        # 连续多次健康检查
        health_checks = []
        for _ in range(5):
            response = api_client.get("/health")
            health_checks.append(response.status_code == 200)
            time.sleep(0.1)

        success_rate = sum(health_checks) / len(health_checks)
        print(f"   健康检查成功率: {success_rate:.1%}")

        assert success_rate >= 0.8, f"健康检查成功率过低: {success_rate:.1%}"
        print("✅ 系统健康监控正常")

    def test_service_availability_monitoring(self, api_client):
        """测试服务可用性监控"""
        print("📝 测试服务可用性监控")

        # 测试关键端点的可用性
        endpoints = ["/health", "/version", "/"]
        availability_results = {}

        for endpoint in endpoints:
            response = api_client.get(endpoint)
            availability_results[endpoint] = response.status_code == 200
            print(f"   {endpoint}: {'✅' if availability_results[endpoint] else '❌'}")

        overall_availability = sum(availability_results.values()) / len(
            availability_results
        )
        assert overall_availability == 1.0, "Some endpoints are not available"

        print("✅ 所有关键端点可用")


if __name__ == "__main__":
    # 运行端到端测试时显示详细输出
    pytest.main([__file__, "-v", "-s"])
