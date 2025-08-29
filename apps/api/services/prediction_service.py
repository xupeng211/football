import logging
from typing import Any, Optional

from models.predictor import Predictor

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(self) -> None:
        self._predictor: Optional[Predictor] = None

    def set_predictor(self, predictor: Predictor) -> None:
        """Sets the predictor instance for the service."""
        self._predictor = predictor

    def _get_predictor(self) -> Predictor:
        """Returns the active predictor, raising an error if it's not set."""
        if self._predictor is None:
            raise RuntimeError("Predictor is not initialized.")
        return self._predictor

    def predict(self, request_data: dict) -> dict[str, Any]:
        """Generates predictions by delegating to the predictor."""
        predictor = self._get_predictor()
        return predictor.predict(request_data)

    def get_model_version(self) -> str | None:
        """Returns the version of the loaded model, if any."""
        if self._predictor:
            return self._predictor.model_version
        return None


# Instantiate the service to be used as a singleton
prediction_service = PredictionService()
