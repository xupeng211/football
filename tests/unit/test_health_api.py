"""
Tests for the health API router.
"""

from fastapi.testclient import TestClient

from football_predict_system.api.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "warning", "unhealthy"]
    assert "timestamp" in data
    assert "version" in data
    assert "components" in data
