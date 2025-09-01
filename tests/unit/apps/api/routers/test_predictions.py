"""
Unit tests for the prediction API endpoints.
"""

from unittest.mock import patch

import pytest
from apps.api.main import app
from apps.api.services.prediction_service import prediction_service
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Provides a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def single_prediction_input() -> dict:
    """Provides a valid input for a single prediction."""
    return {
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "match_date": "2025-08-30",
        "home_odds": 2.1,
        "draw_odds": 3.3,
        "away_odds": 3.2,
    }


@pytest.fixture
def batch_prediction_input() -> dict:
    """Provides a valid input for batch predictions."""
    return {
        "matches": [
            {
                "home_team": "Man City",
                "away_team": "Liverpool",
                "match_date": "2025-08-31",
                "home_odds": 1.8,
                "draw_odds": 3.8,
                "away_odds": 4.0,
            }
        ]
    }


@patch.object(prediction_service, "predict")
def test_predict_single_endpoint(mock_predict, client, single_prediction_input) -> None:
    """Tests the /predict/single endpoint for a successful prediction."""
    mock_predict.return_value = {"predicted_outcome": "away_win", "confidence": 0.7}

    response = client.post("/api/v1/predict/single", json=single_prediction_input)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["predicted_outcome"] == "away_win"
    assert response_data["confidence"] == pytest.approx(0.7)
    mock_predict.assert_called_once()


@patch.object(prediction_service, "predict")
def test_predict_batch_endpoint(mock_predict, client, batch_prediction_input) -> None:
    """Tests the /predict/batch endpoint for successful batch predictions."""
    mock_predict.return_value = {"predicted_outcome": "home_win", "confidence": 0.6}

    response = client.post("/api/v1/predict/batch", json=batch_prediction_input)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total_matches"] == 1
    assert len(response_data["predictions"]) == 1
    prediction = response_data["predictions"][0]
    assert prediction["predicted_outcome"] == "home_win"
    assert prediction["confidence"] == pytest.approx(0.6)
    mock_predict.assert_called_once()


def test_predict_single_invalid_input(client) -> None:
    """Tests the /predict/single endpoint with invalid input data."""
    invalid_input = {"home_team": "Team A", "away_team": "Team B"}
    response = client.post("/api/v1/predict/single", json=invalid_input)
    assert response.status_code == 422  # Unprocessable Entity
