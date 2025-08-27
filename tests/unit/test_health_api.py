"""
Tests for the health API router.
"""

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert data["components"]["database"]["status"] == "unknown"
