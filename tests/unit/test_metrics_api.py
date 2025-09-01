"""
Tests for the metrics API router.
"""

from football_predict_system.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_get_version():
    """Test the version endpoint."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "api_version" in data
    assert "model_version" in data
    assert "model_info" in data
