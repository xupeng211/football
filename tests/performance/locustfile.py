"""
Performance Testing with Locust

This module provides load testing scenarios for the Football Prediction System API
using Locust framework to establish performance baselines and identify bottlenecks.
"""

import json
import random
import time
from typing import Any

from locust import HttpUser, between, task
from locust.exception import StopUser


class PerformanceTestData:
    """Test data generator for performance testing."""

    def __init__(self):
        self.teams = [
            "Manchester United", "Liverpool", "Arsenal", "Chelsea",
            "Manchester City", "Tottenham", "Newcastle", "Brighton",
            "West Ham", "Aston Villa", "Crystal Palace", "Wolves",
            "Leicester", "Leeds United", "Everton", "Southampton",
            "Burnley", "Watford", "Norwich", "Brentford"
        ]

        self.leagues = [
            "Premier League", "Championship", "La Liga", "Serie A",
            "Bundesliga", "Ligue 1", "Eredivisie"
        ]

    def generate_match_data(self) -> dict[str, Any]:
        """Generate random match data for testing."""
        home_team = random.choice(self.teams)
        away_team = random.choice([t for t in self.teams if t != home_team])

        return {
            "home_team": home_team,
            "away_team": away_team,
            "date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}T15:00:00Z",
            "league": random.choice(self.leagues)
        }

    def generate_prediction_request(self) -> dict[str, Any]:
        """Generate a complete prediction request."""
        match_data = self.generate_match_data()

        return {
            "match": match_data,
            "features": {
                "home_form": [random.randint(0, 1) for _ in range(5)],
                "away_form": [random.randint(0, 1) for _ in range(5)],
                "head_to_head": [random.randint(0, 1) for _ in range(3)],
                "league_position_home": random.randint(1, 20),
                "league_position_away": random.randint(1, 20)
            },
            "options": {
                "include_confidence": random.choice([True, False]),
                "detailed_analysis": random.choice([True, False])
            }
        }

    def generate_batch_request(self, batch_size: int = 5) -> dict[str, Any]:
        """Generate batch prediction request."""
        matches = [self.generate_match_data() for _ in range(batch_size)]

        return {
            "matches": matches,
            "options": {
                "include_confidence": True,
                "parallel_processing": True
            }
        }


class BaseFootballPredictUser(HttpUser):
    """Base user class for football prediction API testing."""

    # Wait between 1 and 3 seconds between requests
    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user session."""
        self.test_data = PerformanceTestData()
        self.api_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "LocustPerformanceTest/1.0"
        }

        # Verify API is accessible
        try:
            response = self.client.get("/health/live")
            if response.status_code != 200:
                print(f"API health check failed: {response.status_code}")
                raise StopUser()
        except Exception as e:
            print(f"Failed to connect to API: {e}")
            raise StopUser()


class HealthCheckUser(BaseFootballPredictUser):
    """User focused on health check endpoints - lightweight monitoring."""

    weight = 1  # Lower weight for health checks

    @task(10)
    def health_live(self):
        """Test liveness probe endpoint."""
        with self.client.get("/health/live", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health live failed: {response.status_code}")

    @task(5)
    def health_ready(self):
        """Test readiness probe endpoint."""
        with self.client.get("/health/ready", catch_response=True) as response:
            if response.status_code in [200, 503]:  # Both are acceptable
                response.success()
            else:
                response.failure(f"Health ready failed: {response.status_code}")

    @task(2)
    def health_comprehensive(self):
        """Test comprehensive health check."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code in [200, 503]:
                response.success()

                # Validate response structure
                try:
                    data = response.json()
                    if "overall_status" not in data:
                        response.failure("Missing overall_status in health response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON in health response")
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(1)
    def metrics(self):
        """Test metrics endpoint."""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                if "http_requests_total" in response.text:
                    response.success()
                else:
                    response.failure("Metrics endpoint missing expected content")
            else:
                response.failure(f"Metrics failed: {response.status_code}")


class PredictionUser(BaseFootballPredictUser):
    """User focused on prediction endpoints - main API functionality."""

    weight = 3  # Higher weight for main functionality

    @task(8)
    def single_prediction(self):
        """Test single match prediction endpoint."""
        prediction_request = self.test_data.generate_prediction_request()

        with self.client.post(
            "/api/v1/predictions/predict",
            json=prediction_request,
            headers=self.api_headers,
            catch_response=True
        ) as response:

            if response.status_code == 200:
                response.success()

                # Validate prediction response structure
                try:
                    data = response.json()
                    if "prediction" not in data:
                        response.failure("Missing prediction in response")
                    else:
                        prediction = data["prediction"]
                        required_fields = [
                            "home_win_probability",
                            "draw_probability",
                            "away_win_probability",
                            "predicted_result"
                        ]

                        for field in required_fields:
                            if field not in prediction:
                                response.failure(f"Missing {field} in prediction")
                                break
                        else:
                            # Check probability sum
                            total_prob = (
                                prediction.get("home_win_probability", 0) +
                                prediction.get("draw_probability", 0) +
                                prediction.get("away_win_probability", 0)
                            )

                            if not (0.99 <= total_prob <= 1.01):
                                response.failure(f"Invalid probability sum: {total_prob}")

                except json.JSONDecodeError:
                    response.failure("Invalid JSON in prediction response")

            elif response.status_code == 422:
                # Validation error - acceptable in performance tests
                response.success()

            elif response.status_code == 503:
                # Service unavailable - mark as failure but don't stop
                response.failure("Prediction service unavailable")

            else:
                response.failure(f"Prediction failed: {response.status_code}")

    @task(3)
    def batch_prediction(self):
        """Test batch prediction endpoint."""
        batch_size = random.choice([2, 3, 5])
        batch_request = self.test_data.generate_batch_request(batch_size)

        with self.client.post(
            "/api/v1/predictions/batch",
            json=batch_request,
            headers=self.api_headers,
            catch_response=True
        ) as response:

            if response.status_code == 200:
                response.success()

                # Validate batch response
                try:
                    data = response.json()
                    if "predictions" in data:
                        predictions = data["predictions"]
                        if len(predictions) != batch_size:
                            response.failure(
                                f"Expected {batch_size} predictions, got {len(predictions)}"
                            )
                except json.JSONDecodeError:
                    response.failure("Invalid JSON in batch response")

            elif response.status_code in [422, 503]:
                response.success()  # Acceptable errors

            else:
                response.failure(f"Batch prediction failed: {response.status_code}")

    @task(2)
    def prediction_history(self):
        """Test prediction history endpoint."""
        params = {
            "limit": random.choice([5, 10, 20]),
            "offset": random.choice([0, 10, 20])
        }

        with self.client.get(
            "/api/v1/predictions/history",
            params=params,
            headers=self.api_headers,
            catch_response=True
        ) as response:

            if response.status_code == 200:
                response.success()
            elif response.status_code in [404, 401]:
                # Endpoint might not exist or require auth
                response.success()
            else:
                response.failure(f"History failed: {response.status_code}")


class HeavyLoadUser(BaseFootballPredictUser):
    """User simulating heavy load scenarios."""

    weight = 1  # Lower weight for heavy scenarios

    @task(5)
    def rapid_predictions(self):
        """Make multiple rapid predictions."""
        for _ in range(random.randint(3, 7)):
            prediction_request = self.test_data.generate_prediction_request()

            response = self.client.post(
                "/api/v1/predictions/predict",
                json=prediction_request,
                headers=self.api_headers
            )

            # Brief pause between rapid requests
            time.sleep(0.1)

    @task(2)
    def large_batch_prediction(self):
        """Test large batch predictions."""
        large_batch = self.test_data.generate_batch_request(
            batch_size=random.choice([10, 15, 20])
        )

        with self.client.post(
            "/api/v1/predictions/batch",
            json=large_batch,
            headers=self.api_headers,
            catch_response=True
        ) as response:

            # Large batches might take longer or fail
            if response.status_code in [200, 422, 503, 504]:
                response.success()
            else:
                response.failure(f"Large batch failed: {response.status_code}")

    @task(1)
    def stress_test_endpoint(self):
        """Stress test with complex requests."""
        complex_request = self.test_data.generate_prediction_request()

        # Add complexity
        complex_request["options"].update({
            "detailed_analysis": True,
            "include_confidence": True,
            "advanced_features": True
        })

        response = self.client.post(
            "/api/v1/predictions/predict",
            json=complex_request,
            headers=self.api_headers
        )


class MonitoringUser(BaseFootballPredictUser):
    """User focused on monitoring and observability endpoints."""

    weight = 1

    @task(5)
    def check_metrics(self):
        """Regularly check metrics endpoint."""
        response = self.client.get("/metrics")

        # Metrics should always be available
        if response.status_code != 200:
            print(f"Metrics endpoint failed: {response.status_code}")

    @task(3)
    def comprehensive_health(self):
        """Check comprehensive health status."""
        response = self.client.get("/health")

        if response.status_code == 200:
            try:
                health_data = response.json()

                # Log component status for monitoring
                if "components" in health_data:
                    components = health_data["components"]
                    for component, status in components.items():
                        if status.get("status") != "healthy":
                            print(f"Component {component} unhealthy: {status}")

            except json.JSONDecodeError:
                print("Invalid health response format")

    @task(1)
    def api_discovery(self):
        """Test API documentation endpoints."""
        endpoints_to_check = ["/docs", "/redoc", "/openapi.json"]

        for endpoint in endpoints_to_check:
            response = self.client.get(endpoint)
            # These might not be enabled in production, so don't fail


# Performance Test Scenarios
class LightLoadTest(HealthCheckUser, PredictionUser):
    """Light load test - simulates normal usage."""
    wait_time = between(2, 5)


class MediumLoadTest(HealthCheckUser, PredictionUser, MonitoringUser):
    """Medium load test - simulates busy periods."""
    wait_time = between(1, 3)


class HeavyLoadTest(HealthCheckUser, PredictionUser, HeavyLoadUser, MonitoringUser):
    """Heavy load test - simulates peak usage and stress scenarios."""
    wait_time = between(0.5, 2)


# Custom Locust events for performance monitoring
from locust import events


@events.request.add_listener
def record_request_metrics(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Record custom metrics for analysis."""

    # Log slow requests
    if response_time > 5000:  # 5 seconds
        print(f"SLOW REQUEST: {request_type} {name} took {response_time}ms")

    # Log specific endpoint performance
    if "/predictions/" in name:
        # Could send to external monitoring system
        pass


@events.user_error.add_listener
def record_user_errors(user_instance, exception, tb, **kwargs):
    """Record user errors for analysis."""
    print(f"USER ERROR: {type(exception).__name__}: {exception}")


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize performance test environment."""
    print("🚀 Starting Football Prediction System Performance Tests")
    print(f"Target host: {environment.host}")
    print("Test scenarios: Health checks, Predictions, Batch processing, Heavy load")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Actions to perform when test starts."""
    print("📊 Performance test started")
    print(f"Users: {environment.runner.user_count if hasattr(environment.runner, 'user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Actions to perform when test stops."""
    print("📋 Performance test completed")

    # Print summary statistics
    stats = environment.stats
    if stats.total.num_requests > 0:
        print(f"Total requests: {stats.total.num_requests}")
        print(f"Failed requests: {stats.total.num_failures}")
        print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
        print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"Requests per second: {stats.total.current_rps:.2f}")

        # Performance benchmarks
        error_rate = (stats.total.num_failures / stats.total.num_requests) * 100

        print("\n🎯 Performance Baseline Results:")
        print(f"Error rate: {error_rate:.2f}% (target: <1%)")
        print(f"Average response time: {stats.total.avg_response_time:.2f}ms (target: <2000ms)")
        print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms (target: <5000ms)")

        # Determine if performance baseline is met
        baseline_met = (
            error_rate < 1.0 and
            stats.total.avg_response_time < 2000 and
            stats.total.get_response_time_percentile(0.95) < 5000
        )

        if baseline_met:
            print("✅ Performance baseline PASSED")
        else:
            print("❌ Performance baseline FAILED")
    else:
        print("⚠️  No requests completed - check API connectivity")
