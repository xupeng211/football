"""Unit tests for health API endpoints."""

from fastapi.testclient import TestClient

from football_predict_system.core.constants import HTTPStatus
from football_predict_system.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "warning", "unhealthy"]
    assert "timestamp" in data
    assert "version" in data
    assert "components" in data
