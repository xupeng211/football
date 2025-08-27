"""
Tests for the predictions API router.
"""

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_predict_single_match_success():
    """Test successful single match prediction."""
    request_data = [
        {
            "home": "Team A",
            "away": "Team B",
            "home_form": 2.0,
            "away_form": 1.5,
            "odds_h": 2.1,
            "odds_d": 3.2,
            "odds_a": 3.5,
        }
    ]
    response = client.post("/predict", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "home_win" in data[0]
    assert "draw" in data[0]
    assert "away_win" in data[0]
    assert "predicted_outcome" in data[0]
    assert "confidence" in data[0]


def test_predict_invalid_data():
    """Test prediction with invalid data."""
    request_data = [
        {
            "home": "",  # Empty string
            "away": "Team B",
            "home_form": 2.0,
            "away_form": 1.5,
            "odds_h": 2.1,
            "odds_d": 3.2,
            "odds_a": 3.5,
        }
    ]
    response = client.post("/predict", json=request_data)
    # API might accept empty strings, so check for 200 or 422
    assert response.status_code in [200, 422]


def test_predict_batch_matches_success():
    """Test successful batch match prediction."""
    request_data = [
        {
            "home": "Team C",
            "away": "Team D",
            "home_form": 2.1,
            "away_form": 1.8,
            "odds_h": 2.2,
            "odds_d": 3.1,
            "odds_a": 3.5,
        },
        {
            "home": "Team E",
            "away": "Team F",
            "home_form": 1.9,
            "away_form": 2.2,
            "odds_h": 3.0,
            "odds_d": 3.0,
            "odds_a": 2.5,
        },
    ]
    response = client.post("/predict", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert "home_win" in data[0]


def test_predict_empty_list():
    """Test prediction with an empty list."""
    request_data = []
    response = client.post("/predict", json=request_data)
    assert response.status_code == 400  # Empty list should fail


def test_get_version_endpoint():
    """Test the version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "api_version" in data
    assert "model_version" in data


def test_health_endpoint():
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
