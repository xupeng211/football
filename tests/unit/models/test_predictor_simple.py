"""
简化的预测器测试,专注于提升测试覆盖率
"""

import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from models.predictor import Predictor, _create_feature_vector


class TestPredictorSimple(unittest.TestCase):
    """简化的预测器测试"""

    def test_create_feature_vector(self) -> None:
        """测试特征向量创建"""
        data = {"home_odds": 2.0, "draw_odds": 3.0, "away_odds": 4.0}

        result = _create_feature_vector(data)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

        # 检查计算的特征
        self.assertAlmostEqual(result["implied_prob_home"].iloc[0], 0.5)
        self.assertAlmostEqual(result["implied_prob_draw"].iloc[0], 1 / 3)
        self.assertAlmostEqual(result["implied_prob_away"].iloc[0], 0.25)

        # 检查其他特征
        self.assertEqual(result["fav_flag"].iloc[0], 1)  # home < away
        self.assertAlmostEqual(result["odds_spread_home"].iloc[0], -2.0)

    def test_stub_model_predict(self) -> None:
        """测试存根模型的预测功能"""
        from models.predictor import _StubModel

        stub_model = _StubModel()
        X = pd.DataFrame([{"feature1": 1, "feature2": 2}])

        result = stub_model.predict_proba(X)

        self.assertEqual(result.shape, (1, 3))
        self.assertAlmostEqual(np.sum(result[0]), 1.0, places=2)

    @patch.object(Predictor, "_find_latest_model_dir")
    @patch.object(Predictor, "load_model")
    def test_predictor_with_stub_model(self, mock_load: Mock, mock_find: Mock) -> None:
        """测试使用存根模型的预测器"""
        # 模拟找不到模型
        mock_find.return_value = None

        predictor = Predictor()

        # 验证使用了存根模型
        self.assertEqual(predictor.model_version, "stub-fallback")

        # 测试预测
        data = {"home_odds": 2.0, "draw_odds": 3.0, "away_odds": 4.0}

        result = predictor.predict(data)

        self.assertIn("probabilities", result)
        self.assertIn("predicted_outcome", result)
        self.assertIn("confidence", result)
        self.assertIn("model_version", result)

        self.assertEqual(result["model_version"], "stub-fallback")

    def test_predictor_missing_data_error(self) -> None:
        """测试缺少必要数据时的错误处理"""
        predictor = Predictor()

        # 缺少必要字段
        incomplete_data = {"home_odds": 2.0}

        with self.assertRaises(ValueError):
            predictor.predict(incomplete_data)


if __name__ == "__main__":
    unittest.main()
