import json
import os
import pickle
from dataclasses import dataclass
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import psycopg2
import structlog
import xgboost as xgb
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from apps.api.core.logging import setup_logging

logger = structlog.get_logger()


@dataclass
class TrainingConfig:
    """Configuration for the training process."""

    test_size: float = 0.2
    random_state: int = 42
    n_estimators: int = 100
    max_depth: int = 5
    learning_rate: float = 0.1
    objective: str = "multi:softprob"
    num_class: int = 3
    eval_metric: str = "mlogloss"


class XGBoostTrainer:
    """XGBoost Trainer"""

    def __init__(self, config: TrainingConfig) -> None:
        """Initialize the trainer with a given configuration."""
        self.config = config
        self.model = xgb.XGBClassifier(
            n_estimators=config.n_estimators,
            max_depth=config.max_depth,
            learning_rate=config.learning_rate,
            objective=config.objective,
            num_class=config.num_class,
            eval_metric=config.eval_metric,
            random_state=config.random_state,
        )
        self.label_encoder = LabelEncoder()
        self.feature_names: list[str] = []

    def load_data(self, db_conn_str: str) -> pd.DataFrame:
        """Loads feature and result data from the database."""
        query = """
        SELECT
            f.payload_json,
            m.result
        FROM features f
        JOIN matches m ON f.match_id = m.id
        WHERE m.result IS NOT NULL;
        """
        try:
            with psycopg2.connect(db_conn_str) as conn:
                df = pd.read_sql_query(query, conn)
                logger.info("Successfully loaded data from database", count=len(df))
                return df
        except psycopg2.Error as e:
            logger.error("Database error while loading data", error=str(e))
            raise

    def prepare_data(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Prepares the data for training."""
        # Expand the JSONB payload into columns
        features_df = df["payload_json"].apply(pd.Series)
        X = features_df.astype(np.float32)

        # Encode the target variable
        y = self.label_encoder.fit_transform(df["result"])

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
        )
        logger.info(
            "Data split into training and testing sets",
            train_size=len(X_train),
            test_size=len(X_test),
        )
        return X_train, X_test, pd.Series(y_train), pd.Series(y_test)

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """Trains the XGBoost model."""
        logger.info("Starting model training...")
        self.feature_names = X_train.columns.tolist()
        self.model.fit(X_train, y_train)
        logger.info("Model training completed.")

    def save_model(self, output_dir: str = "models/artifacts") -> str:
        """Saves the trained model and label encoder."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_version_dir = os.path.join(output_dir, timestamp)
        os.makedirs(model_version_dir, exist_ok=True)

        # Save model
        model_path = os.path.join(model_version_dir, "model.xgb")
        joblib.dump(self.model, model_path)

        # Save label encoder
        encoder_path = os.path.join(model_version_dir, "label_encoder.pkl")
        with open(encoder_path, "wb") as f:
            pickle.dump(self.label_encoder, f)

        # Save feature names
        features_path = os.path.join(model_version_dir, "features.json")
        with open(features_path, "w") as f:
            json.dump(self.feature_names, f)

        logger.info("Model and encoder saved", path=model_version_dir)
        return model_version_dir


def main() -> None:
    """Main function to run the training pipeline."""
    load_dotenv()
    db_conn_str = os.environ.get("DATABASE_URL")
    if not db_conn_str:
        raise ValueError("DATABASE_URL not found in environment variables.")

    # For local script execution, connect to localhost
    db_conn_str_local = db_conn_str.replace("@db:", "@localhost:")

    config = TrainingConfig()
    trainer = XGBoostTrainer(config)

    # Load and prepare data
    data_df = trainer.load_data(db_conn_str_local)
    if data_df.empty:
        logger.warning("No data loaded, skipping training.")
        return

    X_train, _, y_train, _ = trainer.prepare_data(data_df)

    # Train and save model
    trainer.train(X_train, y_train)
    trainer.save_model()


if __name__ == "__main__":
    setup_logging()
    main()
