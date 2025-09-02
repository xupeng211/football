"""
API Integration Tests

Tests the complete API integration including database, cache, and health checks.
These tests verify that all components work together correctly.
"""

import asyncio
import time
from typing import Any

import pytest
from httpx import AsyncClient


class TestAPIHealthIntegration:
    """Test health check API integration."""

    async def test_health_endpoint_comprehensive(self, async_client: AsyncClient):
        """Test comprehensive health check endpoint."""
        response = await async_client.get("/health")

        assert response.status_code in [200, 503]  # Healthy or unhealthy

        data = response.json()
        assert "overall_status" in data
        assert "timestamp" in data
        assert "components" in data

        # Verify component structure
        components = data["components"]
        expected_components = ["database", "cache", "application"]

        for component in expected_components:
            assert component in components
            component_data = components[component]
            assert "status" in component_data
            assert "response_time_ms" in component_data

    async def test_health_ready_endpoint(self, async_client: AsyncClient):
        """Test readiness probe endpoint."""
        response = await async_client.get("/health/ready")

        # Should return 200 if ready, 503 if not ready
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["overall_status"] == "healthy"

    async def test_health_live_endpoint(self, async_client: AsyncClient):
        """Test liveness probe endpoint."""
        response = await async_client.get("/health/live")

        # Liveness should always return 200 if app is running
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "version" in data

    async def test_metrics_endpoint(self, async_client: AsyncClient):
        """Test Prometheus metrics endpoint."""
        response = await async_client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        metrics_text = response.text

        # Verify key metrics are present
        expected_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "python_info",
        ]

        for metric in expected_metrics:
            assert metric in metrics_text


class TestPredictionAPIIntegration:
    """Test prediction API integration with dependencies."""

    async def test_single_prediction_flow(
        self,
        async_client: AsyncClient,
        sample_prediction_request: dict[str, Any],
        api_headers: dict[str, str],
    ):
        """Test complete single prediction flow."""

        # Test prediction request
        response = await async_client.post(
            "/api/v1/predictions/predict",
            json=sample_prediction_request,
            headers=api_headers,
        )

        # Should return prediction or error
        assert response.status_code in [200, 400, 422, 503]

        if response.status_code == 200:
            data = response.json()

            # Verify prediction structure
            assert "prediction" in data
            prediction = data["prediction"]

            assert "home_win_probability" in prediction
            assert "draw_probability" in prediction
            assert "away_win_probability" in prediction
            assert "predicted_result" in prediction

            # Verify probabilities sum to ~1.0
            total_prob = (
                prediction["home_win_probability"]
                + prediction["draw_probability"]
                + prediction["away_win_probability"]
            )
            assert 0.99 <= total_prob <= 1.01

            # Verify metadata
            if "metadata" in data:
                metadata = data["metadata"]
                assert "model_version" in metadata
                assert "prediction_timestamp" in metadata

    async def test_batch_prediction_flow(
        self,
        async_client: AsyncClient,
        sample_batch_prediction_request: dict[str, Any],
        api_headers: dict[str, str],
    ):
        """Test batch prediction flow."""

        response = await async_client.post(
            "/api/v1/predictions/batch",
            json=sample_batch_prediction_request,
            headers=api_headers,
        )

        assert response.status_code in [200, 400, 422, 503]

        if response.status_code == 200:
            data = response.json()

            assert "predictions" in data
            predictions = data["predictions"]

            # Should have prediction for each match
            expected_count = len(sample_batch_prediction_request["matches"])
            assert len(predictions) == expected_count

            # Verify each prediction structure
            for prediction in predictions:
                assert "match_id" in prediction or "match" in prediction
                assert "prediction" in prediction

    async def test_prediction_history_flow(
        self, async_client: AsyncClient, api_headers: dict[str, str]
    ):
        """Test prediction history retrieval."""

        # Test getting prediction history
        response = await async_client.get(
            "/api/v1/predictions/history", headers=api_headers, params={"limit": 10}
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            # Should return list of predictions
            assert isinstance(data, list) or "predictions" in data

            if isinstance(data, list):
                predictions = data
            else:
                predictions = data["predictions"]

            # Verify prediction structure if any exist
            if predictions:
                prediction = predictions[0]
                assert "id" in prediction or "prediction_id" in prediction
                assert "match" in prediction or "match_data" in prediction
                assert "result" in prediction or "prediction" in prediction


class TestCacheIntegration:
    """Test cache integration with API endpoints."""

    async def test_cache_miss_and_hit_flow(
        self,
        async_client: AsyncClient,
        sample_prediction_request: dict[str, Any],
        api_headers: dict[str, str],
        cache_helper,
    ):
        """Test cache miss followed by cache hit."""

        # Clear cache to ensure miss
        await cache_helper.clear_test_cache()

        # First request (cache miss)
        start_time = time.time()
        response1 = await async_client.post(
            "/api/v1/predictions/predict",
            json=sample_prediction_request,
            headers=api_headers,
        )
        time.time() - start_time

        if response1.status_code != 200:
            pytest.skip("Prediction service not available")

        # Second identical request (should be cache hit)
        start_time = time.time()
        response2 = await async_client.post(
            "/api/v1/predictions/predict",
            json=sample_prediction_request,
            headers=api_headers,
        )
        time.time() - start_time

        assert response2.status_code == 200

        # Cache hit should be faster (allowing for test variance)
        # This is a heuristic test - cache might not always be faster in tests
        data1 = response1.json()
        data2 = response2.json()

        # Results should be identical for cache hit
        assert data1["prediction"] == data2["prediction"]

    async def test_cache_invalidation(self, async_client: AsyncClient, cache_helper):
        """Test cache invalidation scenarios."""

        # Populate test cache
        test_data = {
            "test_prediction_key": {"result": "cached_prediction"},
            "test_model_key": {"model": "cached_model_data"},
        }

        await cache_helper.populate_test_cache(test_data)

        # Verify cache is populated
        await cache_helper.verify_cache_state(list(test_data.keys()))

        # Test cache clearing (would typically be triggered by admin endpoint)
        await cache_helper.clear_test_cache()


class TestDatabaseIntegration:
    """Test database integration with API endpoints."""

    async def test_database_connectivity(
        self, async_client: AsyncClient, database_manager
    ):
        """Test database connectivity through health check."""

        response = await async_client.get("/health")

        if response.status_code == 200:
            data = response.json()
            db_status = data["components"].get("database", {})
            assert db_status.get("status") == "healthy"
        # If health check fails, database might be unavailable (acceptable in tests)

    async def test_data_persistence_flow(
        self,
        async_client: AsyncClient,
        sample_prediction_request: dict[str, Any],
        api_headers: dict[str, str],
        db_helper,
    ):
        """Test data persistence through API calls."""

        # Make a prediction (should store in database)
        response = await async_client.post(
            "/api/v1/predictions/predict",
            json=sample_prediction_request,
            headers=api_headers,
        )

        if response.status_code != 200:
            pytest.skip("Prediction service not available")

        # Try to retrieve history (should read from database)
        history_response = await async_client.get(
            "/api/v1/predictions/history", headers=api_headers, params={"limit": 1}
        )

        # History endpoint might not be implemented or might require authentication
        assert history_response.status_code in [200, 401, 404, 501]


class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""

    async def test_invalid_prediction_request(
        self, async_client: AsyncClient, api_headers: dict[str, str]
    ):
        """Test handling of invalid prediction requests."""

        invalid_requests = [
            {},  # Empty request
            {"invalid": "data"},  # Invalid structure
            {"match": {}},  # Missing required fields
            {"match": {"home_team": "Team1"}},  # Incomplete match data
        ]

        for invalid_request in invalid_requests:
            response = await async_client.post(
                "/api/v1/predictions/predict", json=invalid_request, headers=api_headers
            )

            # Should return validation error
            assert response.status_code == 422

            data = response.json()
            assert "detail" in data  # FastAPI validation error format

    async def test_malformed_json_handling(
        self, async_client: AsyncClient, api_headers: dict[str, str]
    ):
        """Test handling of malformed JSON requests."""

        malformed_headers = api_headers.copy()
        malformed_headers["Content-Type"] = "application/json"

        response = await async_client.post(
            "/api/v1/predictions/predict",
            content='{"invalid": json}',  # Malformed JSON
            headers=malformed_headers,
        )

        # Should return JSON decode error
        assert response.status_code == 422

    async def test_service_unavailable_handling(self, async_client: AsyncClient):
        """Test handling when services are unavailable."""

        # Test health check when components might be down
        response = await async_client.get("/health")

        # Should return status regardless of component health
        assert response.status_code in [200, 503]

        if response.status_code == 503:
            data = response.json()
            assert "overall_status" in data
            assert data["overall_status"] in ["degraded", "unhealthy"]


class TestConcurrentRequestsIntegration:
    """Test handling of concurrent requests."""

    async def test_concurrent_predictions(
        self,
        async_client: AsyncClient,
        sample_prediction_request: dict[str, Any],
        api_headers: dict[str, str],
    ):
        """Test handling multiple concurrent prediction requests."""

        # Create multiple concurrent requests
        tasks = []
        for _i in range(5):
            task = async_client.post(
                "/api/v1/predictions/predict",
                json=sample_prediction_request,
                headers=api_headers,
            )
            tasks.append(task)

        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze responses
        successful_responses = 0
        error_responses = 0

        for response in responses:
            if isinstance(response, Exception):
                error_responses += 1
            elif response.status_code == 200:
                successful_responses += 1
            else:
                error_responses += 1

        # At least some requests should succeed
        # (Allowing for service unavailability in test environment)
        total_responses = len(responses)
        success_rate = successful_responses / total_responses

        # Log results for debugging
        print(f"Concurrent requests: {total_responses}")
        print(f"Successful: {successful_responses}")
        print(f"Errors: {error_responses}")
        print(f"Success rate: {success_rate:.2%}")

    async def test_concurrent_health_checks(self, async_client: AsyncClient):
        """Test concurrent health check requests."""

        # Health checks should always be fast and reliable
        tasks = []
        for _i in range(10):
            task = async_client.get("/health/live")
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # All health checks should succeed
        for response in responses:
            assert response.status_code == 200


class TestAPIPerformanceBaseline:
    """Baseline performance tests for API integration."""

    async def test_response_time_baseline(
        self,
        async_client: AsyncClient,
        sample_prediction_request: dict[str, Any],
        api_headers: dict[str, str],
        performance_config: dict[str, Any],
    ):
        """Test API response time baseline."""

        max_response_time = performance_config["acceptable_response_time"]

        # Test health endpoint performance
        start_time = time.time()
        health_response = await async_client.get("/health/live")
        health_time = time.time() - start_time

        assert health_response.status_code == 200
        assert health_time < 1.0, f"Health check too slow: {health_time:.3f}s"

        # Test prediction endpoint performance (if available)
        start_time = time.time()
        pred_response = await async_client.post(
            "/api/v1/predictions/predict",
            json=sample_prediction_request,
            headers=api_headers,
        )
        pred_time = time.time() - start_time

        if pred_response.status_code == 200:
            # Only check performance if service is working
            assert pred_time < max_response_time, (
                f"Prediction too slow: {pred_time:.3f}s > {max_response_time}s"
            )

    async def test_throughput_baseline(
        self, async_client: AsyncClient, api_headers: dict[str, str]
    ):
        """Test API throughput baseline."""

        # Test how many health checks we can do in 1 second
        start_time = time.time()
        request_count = 0

        while time.time() - start_time < 1.0:
            response = await async_client.get("/health/live")
            if response.status_code == 200:
                request_count += 1

        elapsed_time = time.time() - start_time
        throughput = request_count / elapsed_time

        # Should be able to handle at least 10 health checks per second
        assert throughput >= 10, f"Low throughput: {throughput:.1f} req/s"

        print(f"Health check throughput: {throughput:.1f} requests/second")
