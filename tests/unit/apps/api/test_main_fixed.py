"""
Fixed tests for apps.api.main module based on actual code structure.
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


class TestAppBasics:
    """Test basic app functionality."""

    @patch("apps.api.main.prediction_service")
    @patch("apps.api.main.Predictor")
    def test_app_creation(self, mock_predictor, mock_prediction_service):
        """Test app can be imported and created."""
        from apps.api.main import app

        assert app is not None
        assert app.title == "足球预测API"
        assert app.version == "1.0.0"

    @patch("apps.api.main.prediction_service")
    @patch("apps.api.main.Predictor")
    def test_app_routes_exist(self, mock_predictor, mock_prediction_service):
        """Test essential routes are registered."""
        from apps.api.main import app

        routes = [route.path for route in app.routes]

        assert "/" in routes
        assert "/version" in routes
        assert "/livez" in routes
        assert "/readyz" in routes


class TestVersionEndpoint:
    """Test version endpoint."""

    @patch("apps.api.main.prediction_service")
    @patch("apps.api.main.Predictor")
    def test_version_endpoint(self, mock_predictor, mock_prediction_service):
        """Test version endpoint returns correct data."""
        from apps.api.main import app

        client = TestClient(app)
        response = client.get("/version")

        assert response.status_code == 200
        data = response.json()
        assert "api_version" in data
        assert "model_version" in data
        assert "model_info" in data
        assert data["api_version"] == "1.0.0"


class TestHealthEndpoints:
    """Test health check endpoints."""

    @patch("apps.api.main.prediction_service")
    @patch("apps.api.main.Predictor")
    def test_livez_endpoint(self, mock_predictor, mock_prediction_service):
        """Test liveness probe."""
        from apps.api.main import app

        client = TestClient(app)
        response = client.get("/livez")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @patch("apps.api.main.prediction_service")
    @patch("apps.api.main.Predictor")
    def test_readyz_endpoint(self, mock_predictor, mock_prediction_service):
        """Test readiness probe."""
        from apps.api.main import app

        client = TestClient(app)
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestRootEndpoint:
    """Test root endpoint."""

    @patch("apps.api.main.prediction_service")
    @patch("apps.api.main.Predictor")
    def test_root_endpoint(self, mock_predictor, mock_prediction_service):
        """Test root endpoint returns navigation info."""
        from apps.api.main import app

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data
        assert "version" in data


class TestLifespanEvents:
    """Test application lifespan events."""

    @patch("apps.api.main.prediction_service")
    @patch("apps.api.main.Predictor")
    def test_lifespan_context_manager(self, mock_predictor, mock_prediction_service):
        """Test lifespan context manager exists."""
        from apps.api.main import lifespan

        assert lifespan is not None
        assert callable(lifespan)


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_logging_import(self):
        """Test logging configuration is imported."""
        from apps.api.main import logger

        assert logger is not None


class TestPredictorInitialization:
    """Test predictor initialization."""

    @patch("apps.api.main.Predictor")
    def test_predictor_created_on_startup(self, mock_predictor):
        """Test predictor is created on application startup."""
        from apps.api.main import app

        with TestClient(app) as client:
            assert hasattr(client.app.state, "predictor")
            assert client.app.state.predictor is not None
            mock_predictor.assert_called_once()


class TestAppIntegration:
    """Integration tests."""

    @patch("apps.api.main.prediction_service")
    @patch("apps.api.main.Predictor")
    def test_app_startup_integration(self, mock_predictor, mock_prediction_service):
        """Test app can start up successfully."""
        from apps.api.main import app

        # Mock the prediction service load_models method
        mock_prediction_service.load_models = MagicMock()

        client = TestClient(app)

        # Test that app responds to basic requests
        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/version")
        assert response.status_code == 200

        response = client.get("/livez")
        assert response.status_code == 200
        assert response.status_code == 200
