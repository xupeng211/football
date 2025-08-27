"""
Unit tests for the XGBoostTrainer.
"""

from typing import Tuple
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import xgboost as xgb

from apps.trainer.xgboost_trainer import TrainingConfig, XGBoostTrainer


@pytest.fixture
def sample_training_data() -> tuple[pd.DataFrame, pd.Series]:
    """Provides a sample DataFrame for training."""
    features = pd.DataFrame(
        {
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
            "feature2": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        }
    )
    target = pd.Series([0, 1, 2, 0, 1, 2, 0, 1, 2])
    return features, target


@pytest.fixture
def trainer() -> XGBoostTrainer:
    """Provides an XGBoostTrainer instance with a default config."""
    config = TrainingConfig(n_estimators=10, test_size=0.33, cv_folds=2)
    return XGBoostTrainer(config=config)


def test_trainer_initialization(trainer: XGBoostTrainer) -> None:
    """Tests that the trainer initializes correctly."""
    assert trainer.config.n_estimators == 10
    assert trainer.model is None


def test_prepare_data(
    trainer: XGBoostTrainer,
    sample_training_data: Tuple[pd.DataFrame, pd.Series],
) -> None:
    """Tests the data preparation method."""
    features, target = sample_training_data
    X_train, X_test, y_train, y_test = trainer.prepare_data(features, target)

    assert isinstance(X_train, pd.DataFrame)
    assert isinstance(X_test, pd.DataFrame)
    assert isinstance(y_train, pd.Series)
    assert isinstance(y_test, pd.Series)
    assert len(X_train) == 6
    assert len(X_test) == 3


@patch("apps.trainer.xgboost_trainer.cross_val_score")
def test_train_method(
    mock_cv_score: MagicMock,
    trainer: XGBoostTrainer,
    sample_training_data: Tuple[pd.DataFrame, pd.Series],
) -> None:
    """Tests the main training method."""
    mock_cv_score.return_value = np.array([0.8, 0.9])
    features, target = sample_training_data
    X_train, X_test, y_train, y_test = trainer.prepare_data(features, target)

    result = trainer.train(X_train, X_test, y_train, y_test)

    assert isinstance(result.model, xgb.XGBClassifier)
    assert result.val_score == pytest.approx(0.85)
    assert result.model is not None
