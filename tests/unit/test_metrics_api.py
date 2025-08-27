"""
Tests for the metrics API router.
"""

from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST

from apps.api.main import app

client = TestClient(app)


def test_get_metrics():
    """Test the metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST
    content = response.text
    assert "api_requests_total" in content
    assert "api_request_duration_seconds" in content
    assert "system_uptime_seconds" in content
