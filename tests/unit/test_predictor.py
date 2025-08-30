"""
预测器模块单元测试

测试足球比赛结果预测器的核心功能
"""

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from models.predictor import Predictor


class TestPredictor:
    """预测器测试类"""

    @pytest.fixture
    def sample_match_data(self) -> dict:
        """示例比赛数据"""
        return {
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "home_form": 2.1,
            "away_form": 1.8,
            "home_odds": 2.2,
            "draw_odds": 3.1,
            "away_odds": 3.5,
        }

    @pytest.fixture
    def mock_model(self) -> Mock:
        """Mock机器学习模型"""
        model = Mock()
        model.predict_proba.return_value = np.array([[0.25, 0.30, 0.45]])
        model.predict.return_value = np.array([2])  # away_win
        return model

    def test_predictor_init_with_model_path(self) -> None:
        """测试使用指定模型路径初始化预测器"""
        with patch.object(Predictor, "load_model") as mock_load_model:
            predictor = Predictor(model_dir="test_model.pkl")
            mock_load_model.assert_called_once_with(Path("test_model.pkl"))
            predictor.model_version = Path("test_model.pkl").name
            assert predictor.model_version == "test_model.pkl"

    def test_predictor_init_without_model_path(self) -> None:
        """测试不指定模型路径初始化预测器"""
        with patch.object(
            Predictor,
            "_find_latest_model_dir",
            return_value=Path("latest_model.pkl"),
        ) as mock_find, patch.object(Predictor, "load_model") as mock_load:
            Predictor()
            mock_find.assert_called_once()
            mock_load.assert_called_once_with(Path("latest_model.pkl"))

    def test_predictor_init_no_model_found(self) -> None:
        """测试找不到模型时的初始化"""
        with patch.object(
            Predictor, "_find_latest_model_dir", return_value=None
        ) as mock_find, patch.object(Predictor, "_use_stub_model") as mock_use_stub:
            Predictor()
            mock_find.assert_called_once()
            mock_use_stub.assert_called_once()

    def test_find_latest_model_exists(self) -> None:
        """测试找到最新模型"""
        with patch(
            "pathlib.Path.glob",
            return_value=[Path("models/artifacts/20250829_231646")],
        ):
            predictor = Predictor.__new__(Predictor)
            predictor.models_dir = Path("models/artifacts")
            latest_model_dir = predictor._find_latest_model_dir()
            assert latest_model_dir.name == "20250829_231646"

    def test_predict_single_with_mock_model(
        self, mock_model: Mock, sample_match_data: dict
    ) -> None:
        """测试使用Mock模型进行单次预测"""
        with patch.object(Predictor, "load_model"), patch(
            "data_pipeline.features.build.create_feature_vector"
        ) as mock_feature:
            mock_feature.return_value = pd.DataFrame([[1, 2, 3, 4, 5]])

            predictor = Predictor(model_dir="test_model.pkl")
            predictor.model = mock_model  # Manually set model
            result = predictor.predict(sample_match_data)

            assert isinstance(result, dict)
            assert "probabilities" in result
            assert "H" in result["probabilities"]
            assert "predicted_outcome" in result
            assert "confidence" in result

    def test_predict_probabilities_normalization(
        self, mock_model: Mock, sample_match_data: dict
    ) -> None:
        """测试预测概率归一化"""
        with patch.object(Predictor, "load_model"), patch(
            "data_pipeline.features.build.create_feature_vector"
        ) as mock_feature:
            mock_model.predict_proba.return_value = np.array([[0.2, 0.3, 0.5]])
            mock_feature.return_value = pd.DataFrame([[1, 2, 3, 4, 5]])

            predictor = Predictor(model_dir="test_model.pkl")
            predictor.model = mock_model
            result = predictor.predict(sample_match_data)

            total_prob = sum(result["probabilities"].values())
            assert abs(total_prob - 1.0) < 1e-6

    def test_predict_confidence_calculation(
        self, mock_model: Mock, sample_match_data: dict
    ) -> None:
        """测试置信度计算"""
        with patch.object(Predictor, "load_model"), patch(
            "data_pipeline.features.build.create_feature_vector"
        ) as mock_feature:
            mock_model.predict_proba.return_value = np.array([[0.1, 0.2, 0.7]])
            mock_feature.return_value = pd.DataFrame([[1, 2, 3, 4, 5]])

            predictor = Predictor(model_dir="test_model.pkl")
            predictor.model = mock_model
            predictor.model_version = "test_model.pkl"

            # Mock the label encoder
            mock_encoder = Mock()
            mock_encoder.classes_ = ["home_win", "draw", "away_win"]
            mock_encoder.inverse_transform.return_value = ["away_win"]
            predictor.label_encoder = mock_encoder

            result = predictor.predict(sample_match_data)

            assert result["confidence"] == 0.7
            assert result["predicted_outcome"] == "away_win"

    def test_model_version_tracking(self) -> None:
        """测试模型版本追踪"""
        with patch.object(Predictor, "load_model") as _:
            model_path = "models/v2.1/xgboost_model.pkl"
            predictor = Predictor(model_dir=model_path)
            predictor.model_version = Path(model_path).name
            assert predictor.model_version == "xgboost_model.pkl"
