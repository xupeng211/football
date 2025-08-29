import json
import pickle
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


def _create_feature_vector(data: dict[str, Any]) -> pd.DataFrame:
    """Creates a feature vector from raw odds data for real-time prediction."""
    df = pd.DataFrame([data])

    # 1. Calculate implied probabilities and bookie margin
    df["implied_prob_home"] = 1 / df["home_odds"]
    df["implied_prob_draw"] = 1 / df["draw_odds"]
    df["implied_prob_away"] = 1 / df["away_odds"]
    df["bookie_margin"] = (
        df["implied_prob_home"] + df["implied_prob_draw"] + df["implied_prob_away"] - 1
    )

    # 2. Add additional features (matching feature_engineer.py)
    df["odds_spread_home"] = df["home_odds"] - df["away_odds"]
    df["fav_flag"] = (df["home_odds"] < df["away_odds"]).astype(int)
    df["log_home"] = np.log(df["home_odds"])
    df["log_away"] = np.log(df["away_odds"])
    df["odds_ratio"] = df["home_odds"] / df["away_odds"]
    df["prob_diff"] = df["implied_prob_home"] - df["implied_prob_away"]

    return df


class Predictor:
    """Loads a trained model and makes predictions."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model: Any = None
        self.label_encoder: Any = None
        self.model_version: str | None = None
        self.feature_names: list[str] = []

        if model_dir:
            self.load_model(Path(model_dir))
        else:
            latest_model_dir = self._find_latest_model_dir()
            if latest_model_dir:
                self.load_model(latest_model_dir)
            else:
                warnings.warn("No trained model found, using stub.", stacklevel=2)
                self._use_stub_model()

    def _find_latest_model_dir(self) -> Path | None:
        """Finds the directory of the latest model in models/artifacts."""
        artifacts_dir = Path("models/artifacts")
        if not artifacts_dir.exists():
            return None

        model_dirs = [
            d
            for d in artifacts_dir.iterdir()
            if d.is_dir() and not d.name.startswith((".", "__"))
        ]
        if not model_dirs:
            return None

        latest_dir = max(model_dirs, key=lambda d: d.stat().st_mtime)
        return latest_dir

    def load_model(self, model_dir: Path) -> None:
        """Loads model, encoder, and feature names from a directory."""
        try:
            # Load model
            model_path = model_dir / "model.xgb"
            self.model = joblib.load(model_path)

            # Load label encoder
            encoder_path = model_dir / "label_encoder.pkl"
            with open(encoder_path, "rb") as f:
                self.label_encoder = pickle.load(f)

            # Load feature names
            features_path = model_dir / "features.json"
            with open(features_path) as f:
                self.feature_names = json.load(f)

            self.model_version = model_dir.name
            logger.info("Successfully loaded model", version=self.model_version)

        except FileNotFoundError as e:
            warnings.warn(f"Model files not found in {model_dir}: {e}", stacklevel=2)
            self._use_stub_model()
        except Exception as e:
            warnings.warn(f"Failed to load model from {model_dir}: {e}", stacklevel=2)
            self._use_stub_model()

    def _use_stub_model(self) -> None:
        """Falls back to using a stub model."""
        self.model = _StubModel()
        self.label_encoder = None
        self.model_version = "stub-fallback"
        self.feature_names = []

    def predict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Predicts the outcome of a single match."""
        if self.model is None:
            raise RuntimeError("Predictor is not initialized.")

        # 1. Create feature vector
        try:
            feature_df = _create_feature_vector(data)
        except KeyError as e:
            raise ValueError(f"Missing required field in input data: {e}") from e

        # 2. Align feature columns
        if self.feature_names:
            feature_df = feature_df.reindex(columns=self.feature_names, fill_value=0)
        else:
            warnings.warn(
                "Feature names not loaded, prediction may be inaccurate.", stacklevel=2
            )

        # 3. Predict probabilities
        try:
            proba = self.model.predict_proba(feature_df)[0]
        except Exception as e:
            raise RuntimeError(f"Model prediction failed: {e}") from e

        # 4. Decode results
        if self.label_encoder:
            class_labels = self.label_encoder.classes_
            probabilities = dict(zip(class_labels, proba))
            predicted_class_index = proba.argmax()
            predicted_outcome = self.label_encoder.inverse_transform(
                [predicted_class_index]
            )[0]
            confidence = proba[predicted_class_index]
        else:  # Stub model case
            probabilities = {"H": proba[0], "D": proba[1], "A": proba[2]}
            predicted_outcome = "D"  # Stub default
            confidence = proba[1]

        return {
            "probabilities": probabilities,
            "predicted_outcome": predicted_outcome,
            "confidence": float(confidence),
            "model_version": self.model_version or "unknown",
        }


class _StubModel:
    """A fallback model that returns fixed probabilities."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.array([[0.34, 0.33, 0.33] for _ in range(len(X))])
