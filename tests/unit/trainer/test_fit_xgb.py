"""
Unit tests for the XGBoost model training script.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import xgboost as xgb

from trainer.fit_xgb import (
    evaluate_model,
    load_data_from_db,
    save_model_and_metrics,
    train_xgboost_model,
)


@pytest.fixture
def sample_features_df():
    """Creates a sample DataFrame with features and a target."""
    data = {
        "match_id": range(10),
        "feature_1": np.random.rand(10),
        "feature_2": np.random.rand(10),
        "result": ["H", "D", "A", "H", "D", "A", "H", "D", "A", "H"],
        "id": range(10),
        "created_at": pd.to_datetime(pd.Timestamp.now()),
        "payload_json": [{"stat_1": 1, "stat_2": 2}] * 10,
    }
    return pd.DataFrame(data)


@patch("trainer.fit_xgb.create_engine")
@patch("trainer.fit_xgb.pd.read_sql")
def test_load_data_from_db(mock_read_sql, mock_create_engine, sample_features_df):
    """Tests the database loading and data transformation logic."""
    # Prepare two different dataframes for the mock
    # The function calls read_sql twice, so we need a side_effect
    features_df = sample_features_df.drop(columns=["result"])
    results_df = sample_features_df[["match_id", "result"]]

    # Set the side_effect to return the two dataframes in order
    mock_read_sql.side_effect = [features_df, results_df]

    df = load_data_from_db("mock_db_url")

    assert not df.empty
    assert "target" in df.columns
    assert df["target"].dtype == "int"
    assert df["target"].isin([0, 1, 2]).all()
    assert "stat_1" in df.columns
    assert "stat_2" in df.columns


def test_train_xgboost_model():
    """Tests that the XGBoost model trains without errors."""
    X = pd.DataFrame({"f1": [1, 2, 3], "f2": [4, 5, 6]})
    y = pd.Series([0, 1, 2])
    model = train_xgboost_model(X, y)
    assert isinstance(model, xgb.XGBClassifier)


def test_evaluate_model():
    """Tests the model evaluation logic."""
    X = pd.DataFrame({"f1": np.random.rand(100), "f2": np.random.rand(100)})
    y = pd.Series(np.random.randint(0, 3, 100))
    model = train_xgboost_model(X, y)

    metrics = evaluate_model(model, X, y)

    assert "accuracy" in metrics
    assert "log_loss" in metrics
    assert "roc_auc" in metrics
    assert "classification_report" in metrics
    assert "feature_importance" in metrics
    assert metrics["accuracy"] >= 0.0


@patch("trainer.fit_xgb.pickle.dump")
@patch("trainer.fit_xgb.Path.mkdir")
@patch("builtins.open")
@patch("trainer.fit_xgb.json.dump")
def test_save_model_and_metrics(
    mock_json_dump, mock_open, mock_mkdir, mock_pickle_dump
):
    """Tests that the model and metrics are saved correctly."""
    model = MagicMock()
    metrics = {
        "accuracy": 0.9,
        "log_loss": 0.1,
        "roc_auc": 0.95,
        "classification_report": {},
        "feature_importance": {},
        "n_samples_test": 100,
        "n_features": 10,
    }

    version = save_model_and_metrics(model, metrics)

    assert isinstance(version, str)
    mock_mkdir.assert_called_once()
    mock_pickle_dump.assert_called_once()
    mock_json_dump.assert_called_once()
