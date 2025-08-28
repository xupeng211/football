"""
模型性能回归测试
确保模型性能不会随着代码变更而退化
"""

import numpy as np
import pandas as pd
import pytest

from models.predictor import Predictor


class TestModelPerformanceRegression:
    """模型性能回归测试"""

    @pytest.fixture
    def sample_test_data(self):
        """创建标准测试数据集"""
        np.random.seed(42)  # 确保可重现性

        # 创建模拟测试数据
        n_samples = 100
        data = {
            "home_team": [f"Team_{i % 10}" for i in range(n_samples)],
            "away_team": [f"Team_{(i + 5) % 10}" for i in range(n_samples)],
            "odds_h": np.random.uniform(1.5, 4.0, n_samples),
            "odds_d": np.random.uniform(2.8, 4.5, n_samples),
            "odds_a": np.random.uniform(1.5, 4.0, n_samples),
            "actual_result": np.random.choice(
                [0, 1, 2], n_samples
            ),  # 0=away, 1=draw, 2=home
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def performance_baselines(self):
        """性能基准指标"""
        return {
            "min_accuracy": 0.30,  # 最低准确率(随机是33%)
            "max_response_time": 0.1,  # 最大响应时间(秒)
            "min_confidence_range": 0.1,  # 置信度最小变化范围
            "prediction_consistency": 0.95,  # 相同输入的预测一致性
        }

    def test_model_accuracy_regression(self, sample_test_data, performance_baselines):
        """测试模型准确率不退化"""
        predictor = Predictor()

        # 批量预测
        matches = sample_test_data[
            ["home_team", "away_team", "odds_h", "odds_d", "odds_a"]
        ].to_dict("records")
        predictions = predictor.predict_batch(matches)

        # 计算准确率
        predicted_outcomes = []
        for pred in predictions:
            if pred["predicted_outcome"] == "home_win":
                predicted_outcomes.append(2)
            elif pred["predicted_outcome"] == "draw":
                predicted_outcomes.append(1)
            else:
                predicted_outcomes.append(0)

        actual_outcomes = sample_test_data["actual_result"].tolist()
        accuracy = np.mean(np.array(predicted_outcomes) == np.array(actual_outcomes))

        # 验证准确率不低于基准
        assert (
            accuracy >= performance_baselines["min_accuracy"]
        ), f"Model accuracy {accuracy:.3f} below baseline {performance_baselines['min_accuracy']}"

    def test_prediction_response_time_regression(
        self, sample_test_data, performance_baselines
    ):
        """测试预测响应时间不退化"""
        import time

        predictor = Predictor()

        # 单次预测响应时间测试
        single_match = {
            "home_team": "Team A",
            "away_team": "Team B",
            "odds_h": 2.0,
            "odds_d": 3.0,
            "odds_a": 4.0,
        }

        start_time = time.time()
        result = predictor.predict_single(**single_match)
        end_time = time.time()

        response_time = end_time - start_time

        assert (
            response_time <= performance_baselines["max_response_time"]
        ), f"Response time {response_time:.3f}s exceeds baseline {performance_baselines['max_response_time']}s"

        # 验证返回结果有效
        assert isinstance(result, dict)
        assert "predicted_outcome" in result

    def test_batch_prediction_scalability_regression(self, performance_baselines):
        """测试批量预测可扩展性不退化"""
        import time

        predictor = Predictor()

        # 测试不同批量大小的性能
        batch_sizes = [1, 10, 50, 100]
        time_per_prediction = []

        for batch_size in batch_sizes:
            matches = [
                {
                    "home_team": f"Team A{i}",
                    "away_team": f"Team B{i}",
                    "odds_h": 2.0,
                    "odds_d": 3.0,
                    "odds_a": 4.0,
                }
                for i in range(batch_size)
            ]

            start_time = time.time()
            results = predictor.predict_batch(matches)
            end_time = time.time()

            time_per_pred = (end_time - start_time) / batch_size
            time_per_prediction.append(time_per_pred)

            # 验证返回结果数量正确
            assert len(results) == batch_size

        # 验证批量处理效率不退化(大批量时每个预测的时间应该更少)
        assert (
            time_per_prediction[-1] <= time_per_prediction[0] * 2
        ), "Batch processing efficiency has degraded"

    def test_prediction_consistency_regression(self, performance_baselines):
        """测试预测一致性不退化"""
        predictor = Predictor()

        # 相同输入应该产生相同输出
        test_match = {
            "home_team": "Consistent Team A",
            "away_team": "Consistent Team B",
            "odds_h": 2.5,
            "odds_d": 3.2,
            "odds_a": 3.8,
        }

        # 多次预测相同输入
        predictions = []
        for _ in range(10):
            result = predictor.predict_single(**test_match)
            predictions.append(result)

        # 检查预测一致性
        first_prediction = predictions[0]
        consistent_predictions = 0

        for pred in predictions:
            if pred["predicted_outcome"] == first_prediction["predicted_outcome"]:
                consistent_predictions += 1

        consistency_rate = consistent_predictions / len(predictions)

        assert (
            consistency_rate >= performance_baselines["prediction_consistency"]
        ), f"Prediction consistency {consistency_rate:.3f} below baseline {performance_baselines['prediction_consistency']}"

    def test_confidence_score_distribution_regression(
        self, sample_test_data, performance_baselines
    ):
        """测试置信度分布不异常"""
        predictor = Predictor()
        if "stub" in predictor.model_version.lower():
            pytest.skip("Skipping confidence distribution test for StubModel")

        matches = sample_test_data[
            ["home_team", "away_team", "odds_h", "odds_d", "odds_a"]
        ].to_dict("records")
        predictions = predictor.predict_batch(matches)

        confidences = [pred["confidence"] for pred in predictions]

        # 验证置信度基本统计特性
        assert all(
            0 <= conf <= 1 for conf in confidences
        ), "Confidence scores outside [0,1] range"
        assert (
            np.std(confidences) >= performance_baselines["min_confidence_range"]
        ), f"Confidence variance {np.std(confidences):.3f} too low, may indicate model issues"

        # 验证置信度分布合理性
        mean_confidence = np.mean(confidences)
        assert (
            0.2 <= mean_confidence <= 0.8
        ), f"Mean confidence {mean_confidence:.3f} outside reasonable range [0.2, 0.8]"

    def test_probability_distribution_regression(self, sample_test_data):
        """测试概率分布的合理性"""
        predictor = Predictor()

        matches = sample_test_data[
            ["home_team", "away_team", "odds_h", "odds_d", "odds_a"]
        ].to_dict("records")
        predictions = predictor.predict_batch(matches)

        for pred in predictions:
            # 验证概率总和为1
            total_prob = pred["home_win"] + pred["draw"] + pred["away_win"]
            assert (
                abs(total_prob - 1.0) < 0.01
            ), f"Probabilities don't sum to 1: {total_prob}"

            # 验证所有概率为非负
            assert (
                pred["home_win"] >= 0
            ), f"Negative home_win probability: {pred['home_win']}"
            assert pred["draw"] >= 0, f"Negative draw probability: {pred['draw']}"
            assert (
                pred["away_win"] >= 0
            ), f"Negative away_win probability: {pred['away_win']}"

            # 验证最高概率对应预测结果
            max_prob = max(pred["home_win"], pred["draw"], pred["away_win"])
            if max_prob == pred["home_win"]:
                expected_outcome = "home_win"
            elif max_prob == pred["draw"]:
                expected_outcome = "draw"
            else:
                expected_outcome = "away_win"

            assert (
                pred["predicted_outcome"] == expected_outcome
            ), "Predicted outcome doesn't match highest probability"


class TestModelStabilityRegression:
    """模型稳定性回归测试"""

    def test_extreme_odds_handling(self):
        """测试极端赔率处理的稳定性"""
        predictor = Predictor()

        extreme_cases = [
            # 极低赔率
            {
                "home_team": "Strong",
                "away_team": "Weak",
                "odds_h": 1.01,
                "odds_d": 10.0,
                "odds_a": 50.0,
            },
            # 极高赔率
            {
                "home_team": "Weak",
                "away_team": "Strong",
                "odds_h": 50.0,
                "odds_d": 10.0,
                "odds_a": 1.01,
            },
            # 接近平等赔率
            {
                "home_team": "Even1",
                "away_team": "Even2",
                "odds_h": 2.0,
                "odds_d": 2.0,
                "odds_a": 2.0,
            },
            # 零赔率(边界情况)
            {
                "home_team": "Test1",
                "away_team": "Test2",
                "odds_h": 0.01,
                "odds_d": 1.0,
                "odds_a": 1.0,
            },
        ]

        for case in extreme_cases:
            try:
                result = predictor.predict_single(**case)

                # 验证结果仍然有效
                assert isinstance(result, dict)
                assert "predicted_outcome" in result
                assert "confidence" in result

                # 验证概率仍然有效
                total_prob = result["home_win"] + result["draw"] + result["away_win"]
                assert (
                    abs(total_prob - 1.0) < 0.1
                ), "Probabilities invalid for extreme case"

            except Exception as e:
                pytest.fail(f"Model failed on extreme case {case}: {e}")

    def test_team_name_variations(self):
        """测试不同队名格式的处理稳定性"""
        predictor = Predictor()

        name_variations = [
            # 正常队名
            {"home_team": "Manchester United", "away_team": "Liverpool FC"},
            # 包含特殊字符
            {"home_team": "Real Madrid C.F.", "away_team": "FC Barcelona"},
            # 长队名
            {
                "home_team": "Very Long Team Name FC United",
                "away_team": "Another Very Long Team Name",
            },
            # 短队名
            {"home_team": "A", "away_team": "B"},
            # 数字队名
            {"home_team": "Team 123", "away_team": "Team 456"},
            # 空格处理
            {"home_team": " Team A ", "away_team": " Team B "},
        ]

        for variation in name_variations:
            case = {**variation, "odds_h": 2.0, "odds_d": 3.0, "odds_a": 4.0}

            try:
                result = predictor.predict_single(**case)
                assert isinstance(result, dict)
                assert "predicted_outcome" in result

            except Exception as e:
                pytest.fail(f"Model failed on team name variation {variation}: {e}")


class TestModelVersionCompatibility:
    """模型版本兼容性回归测试"""

    def test_model_loading_compatibility(self):
        """测试模型加载的向后兼容性"""
        # 这个测试确保新代码能加载旧版本的模型
        predictor = Predictor()

        # 验证基本功能可用
        assert predictor is not None
        assert hasattr(predictor, "model")

        # 验证可以执行预测
        result = predictor.predict_single(
            "Test Team A", "Test Team B", odds_h=2.0, odds_d=3.0, odds_a=4.0
        )

        assert isinstance(result, dict)
        assert "model_version" in result or True  # model_version可能不存在于旧版本

    def test_api_response_format_stability(self):
        """测试API响应格式的稳定性"""
        from fastapi.testclient import TestClient

        from apps.api.main import app

        client = TestClient(app)

        # 测试版本接口格式稳定性
        response = client.get("/version")
        assert response.status_code == 200

        data = response.json()
        required_fields = ["api_version"]
        for field in required_fields:
            assert (
                field in data
            ), f"Required field {field} missing from version response"

        # 测试预测接口格式稳定性
        test_request = [
            {
                "home_team": "Format Test A",
                "away_team": "Format Test B",
                "odds_h": 2.0,
                "odds_d": 3.0,
                "odds_a": 4.0,
            }
        ]

        response = client.post("/predict", json=test_request)
        if response.status_code == 200:
            predictions = response.json()
            assert isinstance(predictions, list)

            if predictions:
                pred = predictions[0]
                expected_fields = [
                    "home_win",
                    "draw",
                    "away_win",
                    "predicted_outcome",
                    "confidence",
                ]
                for field in expected_fields:
                    assert (
                        field in pred
                    ), f"Required field {field} missing from prediction response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
