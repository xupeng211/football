"""
End-to-end test for the complete user workflow.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


class TestCompleteUserWorkflow:
    """E2E test for a complete user workflow."""

    @pytest.fixture
    def api_client(self, monkeypatch):
        """Creates a test client for the API with an isolated DB."""
        # Use monkeypatch to set the test database URL environment variable
        monkeypatch.setenv("TEST_DATABASE_URL", "sqlite:///:memory:")
        return TestClient(app)

    @pytest.fixture
    def sample_batch_input(self):
        """Provides a valid input for batch predictions."""
        return {
            "matches": [
                {
                    "home_team": "Team A",
                    "away_team": "Team B",
                    "match_date": "2025-08-30",
                    "home_odds": 2.1,
                    "draw_odds": 3.3,
                    "away_odds": 3.2,
                },
                {
                    "home_team": "Team C",
                    "away_team": "Team D",
                    "match_date": "2025-08-31",
                    "home_odds": 1.9,
                    "draw_odds": 3.5,
                    "away_odds": 4.2,
                },
            ]
        }

    @patch("apps.api.routers.health.check_db_connection", return_value=(True, "OK"))
    @patch("apps.api.routers.health.check_redis_connection", return_value=(True, "OK"))
    @patch("apps.api.routers.health.check_model_registry", return_value=(True, "OK"))
    @patch(
        "apps.api.routers.health.check_prefect_connection_async",
        return_value=(True, "OK"),
    )
    @patch("apps.api.services.prediction_service.prediction_service.predict")
    def test_complete_prediction_workflow(
        self,
        mock_predict,
        mock_check_prefect,
        mock_check_model,
        mock_check_redis,
        mock_check_db,
        api_client,
        sample_batch_input,
    ):
        """Tests the E2E prediction workflow."""
        # Mock the service layer to return predictable dict probabilities
        mock_predict.side_effect = [
            {
                "home_win": 0.4,
                "draw": 0.3,
                "away_win": 0.3,
                "predicted_outcome": "home_win",
                "confidence": 0.4,
                "model_version": "test",
            },
            {
                "home_win": 0.2,
                "draw": 0.2,
                "away_win": 0.6,
                "predicted_outcome": "away_win",
                "confidence": 0.6,
                "model_version": "test",
            },
        ]

        # Step 1: Check system health
        health_response = api_client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # Step 2: Submit a batch prediction request
        prediction_response = api_client.post(
            "/api/v1/predict/batch", json=sample_batch_input
        )
        assert prediction_response.status_code == 200

        # Step 3: Validate the structure and content of the response
        response_data = prediction_response.json()
        assert "predictions" in response_data
        predictions = response_data["predictions"]
        assert len(predictions) == 2

        # Check first prediction
        assert predictions[0]["predicted_outcome"] == "home_win"
        assert predictions[0]["home_team"] == "Team A"
        assert abs(predictions[0]["confidence"] - 0.4) < 1e-9

        # Check second prediction
        assert predictions[1]["predicted_outcome"] == "away_win"
        assert predictions[1]["home_team"] == "Team C"
        assert abs(predictions[1]["confidence"] - 0.6) < 1e-9

        # Step 4: Verify the prediction service was called correctly
        assert mock_predict.call_count == 2

    def test_error_handling_workflow(self, api_client):
        """Tests the error handling for various user inputs."""
        # Scenario 1: Empty batch request
        empty_response = api_client.post("/api/v1/predict/batch", json={"matches": []})
        assert empty_response.status_code == 422  # Validation error

        # Scenario 2: Invalid data format in batch (missing required fields)
        invalid_data = {"matches": [{"home_team": "Team A"}]}
        invalid_response = api_client.post("/api/v1/predict/batch", json=invalid_data)
        assert invalid_response.status_code == 422
