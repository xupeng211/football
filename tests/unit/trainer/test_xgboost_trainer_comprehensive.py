import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from apps.trainer.xgboost_trainer import TrainingConfig, XGBoostTrainer, main

DB_URL_PATCH = patch(
    "apps.trainer.xgboost_trainer.os.environ", {"DATABASE_URL": "dummy_url"}
)


@pytest.fixture
def training_config() -> TrainingConfig:
    """Provides a default TrainingConfig for tests."""
    return TrainingConfig()


@pytest.fixture
def trainer(training_config: TrainingConfig) -> XGBoostTrainer:
    """Provides an XGBoostTrainer instance for tests."""
    return XGBoostTrainer(config=training_config)


def test_trainer_initialization(
    trainer: XGBoostTrainer, training_config: TrainingConfig
) -> None:
    """Test that the XGBoostTrainer is initialized correctly."""
    assert trainer.config == training_config
    params = trainer.model.get_params()
    assert params["n_estimators"] == training_config.n_estimators
    assert params["max_depth"] == training_config.max_depth


@patch("apps.trainer.xgboost_trainer.psycopg2")
@patch("apps.trainer.xgboost_trainer.pd.read_sql_query")
def test_load_data_success(
    mock_read_sql: MagicMock, mock_psycopg2: MagicMock, trainer: XGBoostTrainer
) -> None:
    """Test successful data loading from the database."""
    mock_conn = MagicMock()
    mock_psycopg2.connect.return_value.__enter__.return_value = mock_conn
    trainer.load_data("dummy_connection_string")
    mock_read_sql.assert_called_once()


@patch("apps.trainer.xgboost_trainer.psycopg2")
def test_load_data_db_error(mock_psycopg2: MagicMock, trainer: XGBoostTrainer) -> None:
    """Test that a database error is handled correctly."""
    mock_psycopg2.connect.side_effect = Exception("DB Error")
    with pytest.raises(Exception, match="DB Error"):
        trainer.load_data("dummy_connection_string")


def test_prepare_data(trainer: XGBoostTrainer) -> None:
    """Test the data preparation method."""
    data = {
        "payload_json": [
            {"feature1": 1, "feature2": 2},
            {"feature1": 3, "feature2": 4},
        ],
        "result": ["WIN", "LOSS"],
    }
    df = pd.DataFrame(data)

    X_train, X_test, y_train, y_test = trainer.prepare_data(df)

    assert not X_train.empty
    assert not X_test.empty
    assert not y_train.empty
    assert not y_test.empty
    assert "feature1" in X_train.columns
    assert trainer.label_encoder.classes_[1] == "WIN"


@patch("apps.trainer.xgboost_trainer.xgb.XGBClassifier.fit")
def test_train(mock_fit: MagicMock, trainer: XGBoostTrainer) -> None:
    """Test the model training method."""
    X_train = pd.DataFrame({"feature1": [1, 2, 3]})
    y_train = pd.Series([0, 1, 0])

    trainer.train(X_train, y_train)

    mock_fit.assert_called_once()
    assert trainer.feature_names == ["feature1"]


@patch("apps.trainer.xgboost_trainer.os.makedirs")
@patch("apps.trainer.xgboost_trainer.joblib.dump")
@patch("apps.trainer.xgboost_trainer.pickle.dump")
@patch("builtins.open", new_callable=MagicMock)
def test_save_model(
    mock_open: MagicMock,
    mock_pickle_dump: MagicMock,
    mock_joblib_dump: MagicMock,
    mock_makedirs: MagicMock,
    trainer: XGBoostTrainer,
) -> None:
    """Test that the model, encoder, and features are saved correctly."""
    trainer.feature_names = ["feature1"]
    model_dir = trainer.save_model()

    mock_makedirs.assert_called()
    mock_joblib_dump.assert_called_once()
    mock_pickle_dump.assert_called_once()
    assert "model.xgb" in mock_joblib_dump.call_args[0][1]
    mock_open.assert_any_call(os.path.join(model_dir, "label_encoder.pkl"), "wb")
    assert model_dir.startswith("models/artifacts/")


@patch("apps.trainer.xgboost_trainer.os.environ", {})
@patch("apps.trainer.xgboost_trainer.load_dotenv")
def test_main_no_db_url(mock_load_dotenv: MagicMock) -> None:
    """Test main raises ValueError if DATABASE_URL is not set."""
    with pytest.raises(ValueError, match="DATABASE_URL not found"):
        main()


@patch("apps.trainer.xgboost_trainer.XGBoostTrainer.load_data")
@DB_URL_PATCH
@patch("apps.trainer.xgboost_trainer.load_dotenv")
def test_main_empty_dataframe(
    mock_load_dotenv: MagicMock, mock_load_data: MagicMock
) -> None:
    """Test training is skipped for an empty DataFrame."""
    mock_load_data.return_value = pd.DataFrame()
    main()
    mock_load_data.assert_called_once()


@patch("apps.trainer.xgboost_trainer.XGBoostTrainer.train")
@patch("apps.trainer.xgboost_trainer.XGBoostTrainer.save_model")
@patch("apps.trainer.xgboost_trainer.XGBoostTrainer.prepare_data")
@patch("apps.trainer.xgboost_trainer.XGBoostTrainer.load_data")
@DB_URL_PATCH
@patch("apps.trainer.xgboost_trainer.load_dotenv")
def test_main_full_run(
    mock_load_dotenv: MagicMock,
    mock_load_data: MagicMock,
    mock_prepare_data: MagicMock,
    mock_save_model: MagicMock,
    mock_train: MagicMock,
) -> None:
    """Test a full successful run of the main function."""
    mock_load_data.return_value = pd.DataFrame(
        {"payload_json": [{}], "result": ["WIN"]}
    )
    mock_prepare_data.return_value = (
        pd.DataFrame(),
        pd.DataFrame(),
        pd.Series(),
        pd.Series(),
    )

    main()

    mock_load_data.assert_called_once()
    mock_prepare_data.assert_called_once()
    mock_train.assert_called_once()
    mock_save_model.assert_called_once()
