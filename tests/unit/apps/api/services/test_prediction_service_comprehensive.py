"""
Tests for the refactored PredictionService.
"""

from unittest.mock import MagicMock

import pytest

from apps.api.services.prediction_service import PredictionService
from models.predictor import Predictor


@pytest.fixture
def service() -> PredictionService:
    """Provides a clean PredictionService instance for each test."""
    return PredictionService()


class TestPredictionService:
    def test_set_and_get_predictor(self, service: PredictionService):
        """Test that the predictor can be set and retrieved."""
        mock_predictor = MagicMock(spec=Predictor)
        service.set_predictor(mock_predictor)

        retrieved_predictor = service._get_predictor()

        assert retrieved_predictor is mock_predictor

    def test_get_predictor_raises_error_if_not_set(self, service: PredictionService):
        """Test getting a predictor before it's set raises a RuntimeError."""
        with pytest.raises(RuntimeError, match="Predictor is not initialized."):
            service._get_predictor()

    def test_predict_delegates_to_predictor(self, service: PredictionService):
        """Test that the service's predict method calls the predictor's method."""
        # Arrange
        mock_predictor = MagicMock(spec=Predictor)
        mock_predictor.predict.return_value = {"prediction": "home_win"}
        service.set_predictor(mock_predictor)
        request_data = {"some": "data"}

        # Act
        result = service.predict(request_data)

        # Assert
        mock_predictor.predict.assert_called_once_with(request_data)
        assert result == {"prediction": "home_win"}
