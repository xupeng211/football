"""
Comprehensive tests for apps.api.routers.metrics module.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create test FastAPI app with metrics router."""
    app = FastAPI()
    from apps.api.routers.metrics import router

    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestMetricsEndpoint:
    """Test /metrics endpoint."""

    @patch("apps.api.routers.metrics.psutil.Process")
    @patch("apps.api.routers.metrics.generate_latest")
    def test_get_metrics_success(
        self, mock_generate_latest: Mock, mock_process: Mock, client: TestClient
    ) -> None:
        """Test successful metrics retrieval."""
        mock_process_instance = Mock()
        mock_process.return_value = mock_process_instance
        mock_process_instance.memory_info.return_value = Mock(rss=1024 * 1024 * 100)

        mock_generate_latest.return_value = (
            b"# HELP test_metric Test metric\ntest_metric 1.0"
        )

        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert b"test_metric" in response.content
        mock_process.assert_called_once()
        mock_process_instance.memory_info.assert_called_once()
        mock_generate_latest.assert_called_once()

    @patch("apps.api.routers.metrics.psutil.Process")
    def test_get_metrics_psutil_error(
        self, mock_process: Mock, client: TestClient
    ) -> None:
        """Test metrics endpoint when psutil fails."""
        mock_process.side_effect = Exception("Process error")

        response = client.get("/metrics")

        assert response.status_code == 200

    @patch("apps.api.routers.metrics.generate_latest")
    def test_get_metrics_prometheus_error(
        self, mock_generate_latest: Mock, client: TestClient
    ) -> None:
        """Test metrics endpoint when Prometheus generation fails."""
        mock_generate_latest.side_effect = Exception("Prometheus error")

        response = client.get("/metrics")

        assert response.status_code == 500


class TestHealthMetricsEndpoint:
    """Test /health/metrics endpoint."""

    @patch("apps.api.routers.metrics.psutil.Process")
    @patch("apps.api.routers.metrics.time.time")
    def test_get_health_metrics_success(
        self, mock_time: Mock, mock_process: Mock, client: TestClient
    ) -> None:
        """Test successful health metrics retrieval."""
        mock_process_instance = Mock()
        mock_process.return_value = mock_process_instance
        mock_process_instance.memory_info.return_value = Mock(rss=1024 * 1024 * 100)
        mock_process_instance.cpu_percent.return_value = 15.5
        mock_process_instance.create_time.return_value = 1000
        mock_process_instance.open_files.return_value = [Mock(), Mock()]
        mock_process_instance.connections.return_value = [Mock()]
        mock_time.return_value = 2000

        response = client.get("/health/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["memory_usage_mb"] == 100.0
        assert data["cpu_percent"] == 15.5
        assert data["uptime_seconds"] == 1000
        assert data["open_files"] == 2
        assert data["connections"] == 1

    @patch("apps.api.routers.metrics.psutil.Process")
    def test_get_health_metrics_psutil_error(
        self, mock_process: Mock, client: TestClient
    ) -> None:
        """Test health metrics when psutil fails."""
        mock_process.side_effect = Exception("Process error")

        response = client.get("/health/metrics")

        assert response.status_code == 200
        assert response.json() == {"error": "Failed to retrieve health metrics"}

    @patch("apps.api.routers.metrics.psutil.Process")
    def test_get_health_metrics_partial_failure(
        self, mock_process: Mock, client: TestClient
    ) -> None:
        """Test health metrics when some psutil calls fail."""
        mock_process_instance = Mock()
        mock_process.return_value = mock_process_instance
        mock_process_instance.memory_info.return_value = Mock(rss=1024 * 1024 * 50)
        mock_process_instance.cpu_percent.side_effect = Exception("CPU error")

        response = client.get("/health/metrics")

        assert response.status_code == 200
        assert response.json() == {"error": "Failed to retrieve health metrics"}


class TestPrometheusMetrics:
    """Test Prometheus metrics functionality."""

    def test_request_count_metric_exists(self) -> None:
        """Test REQUEST_COUNT metric exists."""
        from apps.api.routers.metrics import REQUEST_COUNT

        assert REQUEST_COUNT._name == "http_requests"

    def test_request_duration_metric_exists(self) -> None:
        """Test REQUEST_DURATION metric exists."""
        from apps.api.routers.metrics import REQUEST_DURATION

        assert REQUEST_DURATION._name == "http_request_duration_seconds"

    def test_system_uptime_metric_exists(self) -> None:
        """Test SYSTEM_UPTIME metric exists."""
        from apps.api.routers.metrics import SYSTEM_UPTIME

        assert SYSTEM_UPTIME._name == "system_uptime_seconds"

    def test_memory_usage_metric_exists(self) -> None:
        """Test MEMORY_USAGE metric exists."""
        from apps.api.routers.metrics import MEMORY_USAGE

        assert MEMORY_USAGE._name == "memory_usage_bytes"

    def test_custom_registry_exists(self) -> None:
        """Test custom registry is properly configured."""
        from apps.api.routers.metrics import generate_latest, registry

        output = generate_latest(registry).decode("utf-8")
        assert "http_requests_total" in output
        assert "http_request_duration_seconds" in output
        assert "system_uptime_seconds_total" in output
        assert "memory_usage_bytes" in output


class TestMetricsIntegration:
    """Integration tests for metrics module."""

    @patch("apps.api.routers.metrics.psutil.Process")
    def test_metrics_endpoints_integration(
        self, mock_process: Mock, client: TestClient
    ) -> None:
        """Test both metrics endpoints work together."""
        mock_process_instance = Mock()
        mock_process.return_value = mock_process_instance
        mock_process_instance.memory_info.return_value = Mock(rss=1024 * 1024 * 100)
        mock_process_instance.cpu_percent.return_value = 10.0
        mock_process_instance.create_time.return_value = 1000
        mock_process_instance.open_files.return_value = []
        mock_process_instance.connections.return_value = []

        prometheus_response = client.get("/metrics")
        health_response = client.get("/health/metrics")

        assert prometheus_response.status_code == 200
        assert health_response.status_code == 200
        assert "text/plain" in prometheus_response.headers.get("content-type", "")
        assert health_response.headers.get("content-type") == "application/json"

    def test_router_configuration(self) -> None:
        """Test router is properly configured."""
        from apps.api.routers.metrics import router

        routes = [route.path for route in router.routes]
        assert "/metrics" in routes
        assert "/health/metrics" in routes


class TestMetricsErrorHandling:
    """Test error handling in metrics module."""

    @patch("apps.api.routers.metrics.psutil.Process")
    def test_metrics_handles_os_errors(
        self, mock_process: Mock, client: TestClient
    ) -> None:
        """Test metrics handling of OS-level errors."""
        mock_process.side_effect = OSError("OS error")

        # This should not crash the application
        response = client.get("/metrics")
        assert response.status_code == 200

    @patch("apps.api.routers.metrics.psutil", None)
    def test_metrics_handles_import_errors(self, client: TestClient) -> None:
        """Test metrics handling when psutil is not available."""
        response = client.get("/health/metrics")

        assert response.status_code == 200
        assert response.json() == {"error": "psutil not installed, metrics unavailable"}
        assert response.json() == {"error": "psutil not installed, metrics unavailable"}
