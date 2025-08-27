"""
Tests for the predictions API router.
"""

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_predict_single_match_success():
    """Test successful single match prediction."""
    request_data = {
        "home_team": "Team A",
        "away_team": "Team B",
        "match_date": "2024-09-01",
    }
    response = client.post("/predict/single", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["home_team"] == "Team A"
    assert data["away_team"] == "Team B"
    assert data["match_date"] == "2024-09-01"
    assert "prediction_id" in data
    assert "predicted_outcome" in data
    assert "confidence" in data


def test_predict_single_match_invalid_data():
    """Test single match prediction with invalid data."""
    request_data = {
        "home_team": "Team A",
        # Missing away_team and match_date
    }
    response = client.post("/predict/single", json=request_data)
    assert response.status_code == 422  # Unprocessable Entity


def test_predict_batch_matches_success():
    """Test successful batch match prediction."""
    request_data = {
        "matches": [
            {"home_team": "Team C", "away_team": "Team D", "match_date": "2024-09-02"},
            {"home_team": "Team E", "away_team": "Team F", "match_date": "2024-09-03"},
        ]
    }
    response = client.post("/predict/batch", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 2
    assert len(data["predictions"]) == 2
    assert data["predictions"][0]["home_team"] == "Team C"


def test_predict_batch_matches_empty_list():
    """Test batch match prediction with an empty list."""
    request_data = {"matches": []}
    response = client.post("/predict/batch", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] == 0
    assert len(data["predictions"]) == 0


def test_get_prediction_history_success():
    """Test successful retrieval of prediction history."""
    response = client.get("/history?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "total_count" in data
    assert data["limit"] == 5
    assert data["offset"] == 0


def test_get_prediction_history_invalid_params():
    """Test prediction history with invalid query parameters."""
    response = client.get("/history?limit=200&offset=-1")  # limit > 100, offset < 0
    assert response.status_code == 422
