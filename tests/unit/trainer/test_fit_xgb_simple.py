"""
XGBoost训练模块的简化测试
"""

import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
from trainer.fit_xgb import evaluate_model, save_model_and_metrics, train_xgboost_model


class TestXGBoostTrainerSimple(unittest.TestCase):
    """XGBoost训练器简化测试"""

    def test_train_xgboost_model_default_config(self):
        """测试使用默认配置训练模型"""
        # 创建简单的测试数据
        X = pd.DataFrame(
            {
                "feature1": [1, 2, 3, 4, 5],
                "feature2": [2, 4, 6, 8, 10],
            }
        )
        y = pd.Series([0, 1, 2, 0, 1])

        model = train_xgboost_model(X, y)

        # 验证模型被创建
        self.assertIsNotNone(model)

        # 验证模型可以预测
        predictions = model.predict(X)
        self.assertEqual(len(predictions), len(y))

    def test_train_xgboost_model_custom_config(self):
        """测试使用自定义配置训练模型"""
        X = pd.DataFrame(
            {"feature1": [1, 2, 3, 4, 5, 6], "feature2": [2, 4, 6, 8, 10, 12]}
        )
        y = pd.Series([0, 1, 2, 0, 1, 2])

        custom_config = {
            "n_estimators": 50,
            "max_depth": 3,
            "learning_rate": 0.2,
            "random_state": 42,
        }

        model = train_xgboost_model(X, y, custom_config)

        # 验证模型参数
        self.assertEqual(model.n_estimators, 50)
        self.assertEqual(model.max_depth, 3)
        self.assertEqual(model.learning_rate, 0.2)

    def test_evaluate_model(self):
        """测试模型评估功能"""
        # 创建模拟模型
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0, 1, 2, 0, 1])
        mock_model.predict_proba.return_value = np.array(
            [
                [0.8, 0.1, 0.1],
                [0.1, 0.8, 0.1],
                [0.1, 0.1, 0.8],
                [0.7, 0.2, 0.1],
                [0.2, 0.7, 0.1],
            ]
        )
        mock_model.feature_importances_ = np.array([0.6, 0.4])

        X_test = pd.DataFrame(
            {"feature1": [1, 2, 3, 4, 5], "feature2": [2, 4, 6, 8, 10]}
        )
        y_test = pd.Series([0, 1, 2, 0, 1])

        metrics = evaluate_model(mock_model, X_test, y_test)

        # 验证返回的指标
        expected_keys = [
            "accuracy",
            "log_loss",
            "roc_auc",
            "classification_report",
            "feature_importance",
            "n_samples_test",
            "n_features",
        ]
        for key in expected_keys:
            self.assertIn(key, metrics)

        self.assertEqual(metrics["n_samples_test"], 5)
        self.assertEqual(metrics["n_features"], 2)
        self.assertGreaterEqual(metrics["accuracy"], 0.0)
        self.assertLessEqual(metrics["accuracy"], 1.0)

    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    @patch("json.dump")
    @patch("pickle.dump")
    def test_save_model_and_metrics(
        self, mock_pickle_dump, mock_json_dump, mock_mkdir, mock_open
    ):
        """测试模型和指标保存功能"""
        mock_model = Mock()
        metrics = {
            "accuracy": 0.85,
            "log_loss": 0.5,
            "roc_auc": 0.9,
            "n_samples_test": 100,
        }

        # 模拟文件操作
        mock_open.return_value.__enter__.return_value = Mock()

        version = save_model_and_metrics(mock_model, metrics)

        # 验证版本格式
        self.assertTrue(version.startswith("xgb_"))

        # 验证目录创建被调用
        mock_mkdir.assert_called_once()

        # 验证文件保存被调用
        self.assertEqual(mock_open.call_count, 2)  # pkl和json文件
        mock_pickle_dump.assert_called_once()
        mock_json_dump.assert_called_once()

    def test_evaluate_model_feature_importance(self):
        """测试特征重要性计算"""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0, 1, 2])
        mock_model.predict_proba.return_value = np.array(
            [[0.8, 0.1, 0.1], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]]
        )
        # 使用numpy float32类型,测试类型转换
        mock_model.feature_importances_ = np.array([0.7, 0.3], dtype=np.float32)

        X_test = pd.DataFrame(
            {"important_feature": [1, 2, 3], "less_important": [4, 5, 6]}
        )
        y_test = pd.Series([0, 1, 2])

        metrics = evaluate_model(mock_model, X_test, y_test)

        # 验证特征重要性被正确转换为Python float
        feature_importance = metrics["feature_importance"]
        self.assertIsInstance(feature_importance["important_feature"], float)
        self.assertIsInstance(feature_importance["less_important"], float)

        # 验证重要性值
        self.assertAlmostEqual(feature_importance["important_feature"], 0.7)
        self.assertAlmostEqual(feature_importance["less_important"], 0.3)


if __name__ == "__main__":
    unittest.main()
