"""Unit tests for metrics API endpoints."""

from fastapi.testclient import TestClient

from football_predict_system.core.constants import HTTPStatus
from football_predict_system.main import app

client = TestClient(app)


def test_version_endpoint():
    """Test the version endpoint."""
    response = client.get("/version")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "api_version" in data
    assert "model_version" in data
    assert "model_info" in data
