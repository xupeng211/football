"""
预测器模块的全面单元测试
测试所有核心功能和边界条件
"""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from models.predictor import Predictor, _safe_load_or_stub, _StubModel


@patch("models.predictor._safe_load_or_stub", return_value=_StubModel())
class TestPredictor:
    """预测器类的完整单元测试"""

    def test_predictor_initialization(self, mock_safe_load):
        """测试预测器初始化"""
        predictor = Predictor()
        assert predictor is not None
        assert isinstance(predictor.model, _StubModel)
        assert hasattr(predictor, "model_version")
        assert hasattr(predictor, "feature_columns")

    def test_predictor_with_custom_path(self, mock_safe_load):
        """测试使用自定义路径初始化"""
        custom_path = "/custom/model/path"
        predictor = Predictor(model_path=custom_path)
        assert isinstance(predictor.model, _StubModel)
        mock_safe_load.assert_called_with(custom_path)

    def test_load_model_success(self, mock_safe_load):
        """测试成功加载模型"""
        mock_model = Mock()
        mock_safe_load.return_value = mock_model

        predictor = Predictor()
        predictor.load_model("path/to/model.pkl")

        assert predictor.model == mock_model
        mock_safe_load.assert_called_with("path/to/model.pkl")

    def test_predict_single_with_stub_model(self, mock_safe_load):
        """测试使用stub模型进行单次预测"""
        predictor = Predictor()
        result = predictor.predict_single(
            home_team="Team A", away_team="Team B", odds_h=2.0, odds_d=3.0, odds_a=4.0
        )

        assert isinstance(result, dict)
        required_keys = [
            "home_win",
            "draw",
            "away_win",
            "predicted_outcome",
            "confidence",
        ]
        for key in required_keys:
            assert key in result

        total_prob = result["home_win"] + result["draw"] + result["away_win"]
        assert abs(total_prob - 1.0) < 0.01

    def test_predict_batch_empty_input(self, mock_safe_load):
        """测试批量预测空输入"""
        predictor = Predictor()
        result = predictor.predict_batch([])
        assert result == []

    def test_predict_batch_single_match(self, mock_safe_load):
        """测试批量预测单场比赛"""
        predictor = Predictor()
        matches = [
            {
                "home_team": "Team A",
                "away_team": "Team B",
                "odds_h": 2.0,
                "odds_d": 3.0,
                "odds_a": 4.0,
            }
        ]
        result = predictor.predict_batch(matches)
        assert len(result) == 1
        assert isinstance(result[0], dict)

    def test_predict_batch_multiple_matches(self, mock_safe_load):
        """测试批量预测多场比赛"""
        predictor = Predictor()
        matches = [
            {
                "home_team": f"Team A{i}",
                "away_team": f"Team B{i}",
                "odds_h": 2.0,
                "odds_d": 3.0,
                "odds_a": 4.0,
            }
            for i in range(5)
        ]
        result = predictor.predict_batch(matches)
        assert len(result) == 5
        for prediction in result:
            assert isinstance(prediction, dict)

    def test_predict_batch_with_exception(self, mock_safe_load):
        """测试批量预测异常处理"""
        predictor = Predictor()
        invalid_matches = [{"invalid": "data"}]
        result = predictor.predict_batch(invalid_matches)
        assert isinstance(result, list)


class TestSafeLoadOrStub:
    """安全加载函数的单元测试"""

    def test_safe_load_with_none_path(self):
        """测试空路径"""
        with pytest.warns(
            UserWarning, match="Predictor: model path is None, using stub"
        ):
            result = _safe_load_or_stub(None)
        assert isinstance(result, _StubModel)

    @patch("pickle.load")
    @patch("builtins.open", create=True)
    def test_safe_load_success(self, mock_open, mock_pickle_load):
        """测试成功加载模型"""
        mock_model = Mock()
        mock_pickle_load.return_value = mock_model

        result = _safe_load_or_stub("/valid/path.pkl")
        assert result == mock_model

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_safe_load_file_not_found(self, mock_open):
        """测试文件不存在的情况"""
        with pytest.warns(UserWarning, match="missing or corrupt"):
            result = _safe_load_or_stub("/nonexistent/path.pkl")
        assert isinstance(result, _StubModel)

    @patch("pickle.load", side_effect=Exception("Corrupt file"))
    @patch("builtins.open", create=True)
    def test_safe_load_corrupt_file(self, mock_open, mock_pickle_load):
        """测试损坏文件的情况"""
        with pytest.warns(UserWarning, match="missing or corrupt"):
            result = _safe_load_or_stub("/corrupt/file.pkl")
        assert isinstance(result, _StubModel)


class TestStubModel:
    """StubModel的单元测试"""

    def test_stub_model_initialization(self):
        """测试StubModel初始化"""
        stub = _StubModel()
        assert stub is not None

    def test_stub_model_predict_proba(self):
        """测试StubModel的概率预测"""
        stub = _StubModel()

        # 创建模拟特征数据
        features = pd.DataFrame({"feature1": [1, 2, 3], "feature2": [4, 5, 6]})

        result = stub.predict_proba(features)

        # 验证返回结果
        assert isinstance(result, np.ndarray)
        assert result.shape == (3, 3)  # 3行3列(3个类别)

        # 验证每行概率和为1
        for row in result:
            assert abs(np.sum(row) - 1.0) < 0.01

    def test_stub_model_predict(self):
        """测试StubModel的类别预测"""
        stub = _StubModel()

        features = pd.DataFrame({"feature1": [1, 2], "feature2": [3, 4]})

        result = stub.predict(features)

        assert isinstance(result, np.ndarray)
        assert len(result) == 2
        assert all(isinstance(x, (int, np.integer)) for x in result)
        assert all(0 <= x <= 2 for x in result)


# 边界条件和错误处理测试
class TestPredictorEdgeCases:
    """预测器边界条件测试"""

    def test_predictor_with_missing_features(self):
        """测试缺少特征的情况"""
        predictor = Predictor()

        # 只提供部分必需参数
        with pytest.raises(TypeError):
            predictor.predict_single("Team A", "Team B")  # 缺少odds参数

    def test_predictor_with_invalid_odds(self):
        """测试无效赔率的情况"""
        predictor = Predictor()

        # It should raise a ValueError due to invalid odds
        with pytest.raises(
            ValueError, match="输入验证失败: 主胜赔率必须大于0,收到:-1.0"
        ):
            predictor.predict_single(
                "Team A",
                "Team B",
                odds_h=-1,  # 负赔率
                odds_d=0,  # 零赔率
                odds_a=float("inf"),  # 无穷大赔率
            )

    def test_predictor_large_batch(self):
        """测试大批量预测的性能"""
        predictor = Predictor()

        # 创建大批量数据
        large_batch = [
            {
                "home_team": f"Team A{i}",
                "away_team": f"Team B{i}",
                "odds_h": 2.0,
                "odds_d": 3.0,
                "odds_a": 4.0,
            }
            for i in range(100)
        ]

        result = predictor.predict_batch(large_batch)
        assert len(result) == 100

        # 验证所有预测都是有效的
        for prediction in result:
            assert isinstance(prediction, dict)
            assert "confidence" in prediction


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
