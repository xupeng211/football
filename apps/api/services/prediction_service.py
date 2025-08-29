import logging
import pickle  # nosec B403
from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd
import xgboost as xgb

logger = logging.getLogger(__name__)


class PredictionService:
    _models: ClassVar[dict[str, xgb.XGBClassifier]] = {}
    _model_versions: ClassVar[dict[str, str]] = {}

    def list_models(self) -> list[str]:
        """Lists all available models."""
        model_path = Path("models/artifacts")
        if not model_path.exists():
            return []
        return [
            p.name
            for p in model_path.iterdir()
            if p.is_dir() and p.name.startswith("xgb_")
        ]

    def load_model(self, model_name: str) -> None:
        """Loads a specific model into memory."""
        if model_name in self._models:
            return

        model_path = Path(f"models/artifacts/{model_name}/model.pkl")
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        try:
            logger.info(f"Loading model: {model_name}")
            with open(model_path, "rb") as f:
                model = pickle.load(f)  # nosec B301
            self._models[model_name] = model
            self._model_versions[model_name] = model_name
            logger.info(f"Model '{model_name}' loaded successfully.")
        except (FileNotFoundError, pickle.UnpicklingError) as e:
            logger.error(f"Failed to load model '{model_name}': {e}")
            if model_name in self._models:
                del self._models[model_name]
            if model_name in self._model_versions:
                del self._model_versions[model_name]

    def load_models(self) -> None:
        """Loads all available models into memory."""
        for model_name in self.list_models():
            self.load_model(model_name)

    def _generate_inference_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generates a feature DataFrame from prediction request data."""
        # Create a copy to avoid modifying the original DataFrame
        odds_df = data.copy()

        # --- Re-apply the same feature engineering logic from training ---
        # 1. Implied probabilities and margin
        odds_df["implied_prob_home"] = 1 / odds_df["home_odds"]
        odds_df["implied_prob_draw"] = 1 / odds_df["draw_odds"]
        odds_df["implied_prob_away"] = 1 / odds_df["away_odds"]
        odds_df["bookie_margin"] = (
            odds_df["implied_prob_home"]
            + odds_df["implied_prob_draw"]
            + odds_df["implied_prob_away"]
            - 1
        )

        # 2. Additional features
        odds_df["odds_spread_home"] = (
            odds_df["home_odds"] - odds_df["home_odds"].min()
        )  # This will be 0 for a single row
        odds_df["fav_flag"] = (odds_df["home_odds"] < odds_df["away_odds"]).astype(int)
        odds_df["log_home"] = np.log(odds_df["home_odds"])
        odds_df["log_away"] = np.log(odds_df["away_odds"])
        odds_df["odds_ratio"] = odds_df["home_odds"] / odds_df["away_odds"]
        odds_df["prob_diff"] = (
            odds_df["implied_prob_home"] - odds_df["implied_prob_away"]
        )

        # 3. Ensure column order matches model expectation
        feature_columns = [
            "fav_flag",
            "log_away",
            "log_home",
            "prob_diff",
            "odds_ratio",
            "bookie_margin",
            "odds_spread_home",
            "implied_prob_away",
            "implied_prob_draw",
            "implied_prob_home",
        ]
        return odds_df[feature_columns]

    def predict(self, request_data: dict, model_name: str | None = None) -> np.ndarray:
        """Generates predictions for the given input data."""
        if not model_name:
            available_models = self.list_models()
            if not available_models:
                raise RuntimeError("No models available.")
            model_name = max(available_models)

        if model_name not in self._models:
            self.load_model(model_name)

        model = self._models.get(model_name)
        if model is None:
            raise RuntimeError(f"Model '{model_name}' is not loaded.")

        # 1. Generate features from the request data
        features_df = self._generate_inference_features(pd.DataFrame([request_data]))

        # 2. Predict using the generated features
        return model.predict_proba(features_df)

    def predict_batch(
        self, matches_data: list[dict], model_name: str | None = None
    ) -> np.ndarray:
        """Generates predictions for a batch of matches."""
        if not model_name:
            available_models = self.list_models()
            if not available_models:
                raise RuntimeError("No models available.")
            model_name = max(available_models)

        if model_name not in self._models:
            self.load_model(model_name)

        model = self._models.get(model_name)
        if model is None:
            raise RuntimeError(f"Model '{model_name}' is not loaded.")

        # Predict each match individually to respect mocking in tests
        predictions = []
        for match_data in matches_data:
            prediction = self.predict(match_data, model_name=model_name)
            predictions.append(prediction[0])
        return np.array(predictions)


# Instantiate the service to be used as a singleton
prediction_service = PredictionService()
