"""Tests for API v1 endpoints router."""

import pytest
from fastapi.testclient import TestClient

from football_predict_system.api.v1.endpoints import router


@pytest.fixture
def test_app():
    """Create a test FastAPI app with the endpoints router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


class TestEndpointsRouter:
    """Test the API v1 endpoints router."""

    def test_router_creation(self):
        """Test that the router is created successfully."""
        assert router is not None
        assert hasattr(router, 'routes')
        assert len(router.routes) > 0

    def test_status_endpoint(self, client):
        """Test the API status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "v1"

    def test_router_includes_subrouters(self):
        """Test that the router includes the expected subrouters."""
        # Check that predictions and models routers are included
        assert any("/predictions" in str(route) for route in router.routes)
        assert any("/models" in str(route) for route in router.routes)

    def test_router_tags(self):
        """Test that routes have appropriate tags."""
        status_routes = [
            route for route in router.routes
            if hasattr(route, 'path') and route.path == "/status"
        ]
        assert len(status_routes) > 0

        status_route = status_routes[0]
        if hasattr(status_route, 'tags'):
            assert "general" in status_route.tags
