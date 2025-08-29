"""
Tests for the predictions API router.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.prediction_service import prediction_service


@pytest.fixture
def client() -> TestClient:
    """Provides a test client for the FastAPI application."""
    return TestClient(app)


@patch.object(prediction_service, "predict")
def test_predict_single_match_success(
    mock_predict: MagicMock, client: TestClient
) -> None:
    """Test successful single match prediction."""
    test_data = {
        "home_team": "Team A",
        "away_team": "Team B",
        "match_date": "2025-01-01",
        "home_odds": 2.1,
        "draw_odds": 3.2,
        "away_odds": 3.5,
    }
    mock_predict.return_value = np.array([[0.45, 0.30, 0.25]])

    response = client.post("/api/v1/predict/single", json=test_data)
    assert response.status_code == 200
    prediction = response.json()
    assert prediction["predicted_outcome"] == "home_win"


def test_predict_invalid_data(client: TestClient) -> None:
    """Test prediction with invalid data."""
    test_data = {
        "home_team": "Team A",
        # Missing other required fields
    }
    response = client.post("/api/v1/predict/single", json=test_data)
    assert response.status_code == 422


@patch.object(prediction_service, "predict_batch")
def test_predict_batch_matches_success(
    mock_predict_batch: MagicMock, client: TestClient
) -> None:
    """Test successful batch match prediction."""
    test_data = {
        "matches": [
            {
                "home_team": "Team A",
                "away_team": "Team B",
                "match_date": "2025-01-01",
                "home_odds": 2.1,
                "draw_odds": 3.2,
                "away_odds": 3.5,
            }
        ]
    }
    mock_predict_batch.return_value = np.array([[0.45, 0.30, 0.25]])

    response = client.post("/api/v1/predict/batch", json=test_data)
    assert response.status_code == 200
    predictions = response.json()
    assert len(predictions["predictions"]) == 1


def test_predict_empty_list(client: TestClient) -> None:
    """Test prediction with an empty list."""
    response = client.post("/api/v1/predict/batch", json={"matches": []})
    assert response.status_code == 422


def test_get_version_endpoint(client: TestClient) -> None:
    """Test the version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "api_version" in data
    assert "model_version" in data


def test_health_endpoint(client: TestClient) -> None:
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
