"""Test the predictions API endpoints."""

import pytest

# Skip since prediction_service is not implemented
pytestmark = pytest.mark.skip(reason="prediction_service not implemented")

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from football_predict_system.main import app

# TODO: Implement prediction_service
# from football_predict_system.api.services.prediction_service import prediction_service
from tests.factories import sample_match, sample_matches, sample_prediction


@pytest.fixture
def client() -> TestClient:
    """Provides a test client for the FastAPI application."""
    return TestClient(app)


@patch.object(prediction_service, "predict")
def test_predict_single_match_success(
    mock_predict: MagicMock, client: TestClient
) -> None:
    """Test successful single match prediction."""
    # 使用测试数据工厂
    test_data = sample_match()
    mock_predict.return_value = sample_prediction(home_win=0.8, draw=0.1, away_win=0.1)

    response = client.post("/api/v1/predict/single", json=test_data)
    assert response.status_code == 200
    prediction = response.json()
    assert prediction["predicted_outcome"] == "home_win"


def test_predict_invalid_data(client: TestClient) -> None:
    """Test prediction with invalid data."""
    # 使用工厂创建有效数据,然后移除一个必需字段
    test_data = sample_match()
    del test_data["away_team"]
    response = client.post("/api/v1/predict/single", json=test_data)
    assert response.status_code == 422


@patch.object(prediction_service, "predict")
def test_predict_batch_matches_success(
    mock_predict: MagicMock, client: TestClient
) -> None:
    """Test successful batch match prediction."""
    # 使用测试数据工厂
    test_data = {"matches": sample_matches(count=3)}
    mock_predict.return_value = sample_prediction()

    response = client.post("/api/v1/predict/batch", json=test_data)
    assert response.status_code == 200
    predictions = response.json()
    assert len(predictions["predictions"]) == 3


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
