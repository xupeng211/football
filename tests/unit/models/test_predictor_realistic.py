"""
基于实际代码行为的现实预测器测试
"""

import numpy as np
import pandas as pd
import pytest

from models.predictor import Predictor, _safe_load_or_stub, _StubModel


class TestPredictorRealistic:
    """基于实际行为的预测器测试"""

    def test_predictor_initialization(self):
        """测试预测器基本初始化"""
        predictor = Predictor()
        assert predictor is not None
        assert hasattr(predictor, "model")
        assert hasattr(predictor, "model_version")
        assert hasattr(predictor, "feature_columns")

    def test_predictor_with_nonexistent_path_uses_stub(self):
        """测试不存在路径时使用stub模型"""
        predictor = Predictor(model_path="/definitely/nonexistent/path")
        assert isinstance(predictor.model, _StubModel)

    def test_prediction_returns_basic_probabilities(self):
        """测试预测返回基本概率(基于实际格式)"""
        predictor = Predictor(model_path="/nonexistent")

        result = predictor.predict_single(
            home_team="Team A", away_team="Team B", odds_h=2.0, odds_d=3.0, odds_a=4.0
        )

        # 验证实际返回的字段
        assert isinstance(result, dict)
        assert "home_win" in result
        assert "draw" in result
        assert "away_win" in result
        assert "model_version" in result

        # 验证概率值范围
        assert 0 <= result["home_win"] <= 1
        assert 0 <= result["draw"] <= 1
        assert 0 <= result["away_win"] <= 1

        # 验证概率总和接近1
        total = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total - 1.0) < 0.05

    def test_batch_prediction_basic(self):
        """测试批量预测基本功能"""
        predictor = Predictor(model_path="/nonexistent")

        matches = [
            {
                "home_team": "A",
                "away_team": "B",
                "odds_h": 2.0,
                "odds_d": 3.0,
                "odds_a": 4.0,
            },
            {
                "home_team": "C",
                "away_team": "D",
                "odds_h": 1.8,
                "odds_d": 3.2,
                "odds_a": 4.5,
            },
        ]

        results = predictor.predict_batch(matches)
        assert len(results) == 2

        for result in results:
            assert isinstance(result, dict)
            assert "home_win" in result
            assert "draw" in result
            assert "away_win" in result

    def test_empty_batch_prediction(self):
        """测试空批量预测"""
        predictor = Predictor(model_path="/nonexistent")
        result = predictor.predict_batch([])
        assert result == []

    def test_predictor_handles_normal_odds(self):
        """测试处理正常赔率(避免除零错误)"""
        predictor = Predictor(model_path="/nonexistent")

        # 使用安全的赔率值
        result = predictor.predict_single(
            "Team A",
            "Team B",
            odds_h=2.0,  # 安全值
            odds_d=3.0,  # 安全值
            odds_a=4.0,  # 安全值
        )

        assert isinstance(result, dict)
        assert "home_win" in result


class TestStubModelRealistic:
    """基于实际实现的StubModel测试"""

    def test_stub_model_predict_proba_works(self):
        """测试StubModel的predict_proba方法"""
        stub = _StubModel()

        # 使用DataFrame输入
        X = pd.DataFrame({"feature1": [1, 2], "feature2": [3, 4]})
        result = stub.predict_proba(X)

        assert isinstance(result, np.ndarray)
        assert result.shape == (2, 3)  # 2行3列

        # 验证每行是概率分布
        for row in result:
            assert abs(np.sum(row) - 1.0) < 0.01
            assert all(p >= 0 for p in row)


class TestPredictorErrorHandling:
    """预测器错误处理测试"""

    def test_missing_required_params_raises_error(self):
        """测试缺少必需参数抛出错误"""
        predictor = Predictor(model_path="/nonexistent")

        with pytest.raises(TypeError):
            predictor.predict_single("Team A", "Team B")  # 缺少odds

    def test_invalid_odds_causes_error_gracefully(self):
        """测试无效赔率的错误处理"""
        predictor = Predictor(model_path="/nonexistent")

        # This test now expects a ValueError due to the input validation
        with pytest.raises(
            ValueError, match="输入验证失败: 平局赔率必须大于0,收到:0.0"
        ):
            predictor.predict_single(
                "Team A",
                "Team B",
                odds_h=2.0,
                odds_d=0.0,  # 这会导致除零错误
                odds_a=4.0,
            )


class TestSafeLoadFunction:
    """安全加载函数测试"""

    def test_safe_load_nonexistent_returns_stub(self):
        """测试加载不存在文件返回stub"""
        result = _safe_load_or_stub("/definitely/does/not/exist.pkl")
        assert isinstance(result, _StubModel)

    def test_safe_load_none_path_returns_stub(self):
        """测试None路径返回stub"""
        result = _safe_load_or_stub(None)
        assert isinstance(result, _StubModel)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
