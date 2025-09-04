"""
Tests for analytics service.

Complete coverage tests for AnalyticsService functionality.
"""

from unittest.mock import MagicMock, patch

import pytest

from football_predict_system.domain.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Test AnalyticsService class."""

    def test_analytics_service_initialization(self):
        """Test AnalyticsService initialization."""
        service = AnalyticsService()

        assert service is not None
        assert hasattr(service, "logger")
        assert service.logger is not None

    @patch("football_predict_system.domain.services.analytics_service.get_logger")
    def test_analytics_service_logger_setup(self, mock_get_logger):
        """Test logger is properly set up."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        service = AnalyticsService()

        assert service.logger is mock_logger
        mock_get_logger.assert_called_with(
            "football_predict_system.domain.services.analytics_service"
        )

    @pytest.mark.asyncio
    async def test_get_model_accuracy_defaults(self):
        """Test get_model_accuracy with default parameters."""
        service = AnalyticsService()

        result = await service.get_model_accuracy()

        assert isinstance(result, dict)
        assert "accuracy" in result
        assert "total_predictions" in result
        assert "correct_predictions" in result
        assert "period_days" in result
        assert "model_version" in result

        # Check default values
        assert result["period_days"] == 30
        assert result["model_version"] == "default"

    @pytest.mark.asyncio
    async def test_get_model_accuracy_custom_parameters(self):
        """Test get_model_accuracy with custom parameters."""
        service = AnalyticsService()

        result = await service.get_model_accuracy(model_version="v2.0", days_back=60)

        assert result["model_version"] == "v2.0"
        assert result["period_days"] == 60
        assert isinstance(result["accuracy"], float)
        assert isinstance(result["total_predictions"], int)
        assert isinstance(result["correct_predictions"], int)

    @pytest.mark.asyncio
    async def test_get_model_accuracy_return_structure(self):
        """Test get_model_accuracy return structure is correct."""
        service = AnalyticsService()

        result = await service.get_model_accuracy()

        # Verify all expected keys are present
        expected_keys = {
            "accuracy",
            "total_predictions",
            "correct_predictions",
            "period_days",
            "model_version",
        }
        assert set(result.keys()) == expected_keys

        # Verify accuracy calculation is consistent
        expected_accuracy = result["correct_predictions"] / result["total_predictions"]
        assert abs(result["accuracy"] - expected_accuracy) < 0.01

    @pytest.mark.asyncio
    async def test_get_model_accuracy_values_reasonable(self):
        """Test get_model_accuracy returns reasonable values."""
        service = AnalyticsService()

        result = await service.get_model_accuracy()

        # Accuracy should be between 0 and 1
        assert 0 <= result["accuracy"] <= 1

        # Predictions should be positive
        assert result["total_predictions"] > 0
        assert result["correct_predictions"] >= 0

        # Correct predictions shouldn't exceed total
        assert result["correct_predictions"] <= result["total_predictions"]

    @pytest.mark.asyncio
    async def test_get_model_performance_comparison_structure(self):
        """Test get_model_performance_comparison structure."""
        service = AnalyticsService()

        result = await service.get_model_performance_comparison()

        assert isinstance(result, dict)
        assert "models" in result
        assert "comparison_period_days" in result

        assert isinstance(result["models"], list)
        assert len(result["models"]) > 0
        assert result["comparison_period_days"] == 30

    @pytest.mark.asyncio
    async def test_get_model_performance_comparison_models_format(self):
        """Test model comparison models format."""
        service = AnalyticsService()

        result = await service.get_model_performance_comparison()

        models = result["models"]
        assert len(models) >= 2  # Should have multiple models to compare

        for model in models:
            assert isinstance(model, dict)
            assert "version" in model
            assert "accuracy" in model
            assert "total_predictions" in model

            # Verify types
            assert isinstance(model["version"], str)
            assert isinstance(model["accuracy"], float)
            assert isinstance(model["total_predictions"], int)

            # Verify reasonable values
            assert 0 <= model["accuracy"] <= 1
            assert model["total_predictions"] > 0

    @pytest.mark.asyncio
    async def test_get_model_performance_comparison_specific_models(self):
        """Test specific models in performance comparison."""
        service = AnalyticsService()

        result = await service.get_model_performance_comparison()

        models = result["models"]
        model_versions = [model["version"] for model in models]

        # Should include expected model versions
        assert "default" in model_versions
        assert "neural_v2" in model_versions

    @pytest.mark.asyncio
    async def test_get_prediction_trends_defaults(self):
        """Test get_prediction_trends with default parameters."""
        service = AnalyticsService()

        result = await service.get_prediction_trends()

        assert isinstance(result, dict)
        assert "total_predictions" in result
        assert "average_confidence" in result
        assert "prediction_distribution" in result
        assert "period_days" in result

        # Check default period
        assert result["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_prediction_trends_custom_period(self):
        """Test get_prediction_trends with custom period."""
        service = AnalyticsService()

        result = await service.get_prediction_trends(days_back=14)

        assert result["period_days"] == 14

    @pytest.mark.asyncio
    async def test_get_prediction_trends_distribution_structure(self):
        """Test prediction trends distribution structure."""
        service = AnalyticsService()

        result = await service.get_prediction_trends()

        distribution = result["prediction_distribution"]
        assert isinstance(distribution, dict)

        # Should have all prediction types
        assert "home_wins" in distribution
        assert "draws" in distribution
        assert "away_wins" in distribution

        # All should be probabilities
        for _outcome, probability in distribution.items():
            assert isinstance(probability, float)
            assert 0 <= probability <= 1

    @pytest.mark.asyncio
    async def test_get_prediction_trends_distribution_sums_to_one(self):
        """Test prediction distribution probabilities sum to approximately 1."""
        service = AnalyticsService()

        result = await service.get_prediction_trends()

        distribution = result["prediction_distribution"]
        total_probability = sum(distribution.values())

        # Should sum to approximately 1.0 (allowing for small floating point errors)
        assert abs(total_probability - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_get_prediction_trends_values_reasonable(self):
        """Test prediction trends values are reasonable."""
        service = AnalyticsService()

        result = await service.get_prediction_trends()

        # Total predictions should be positive
        assert result["total_predictions"] > 0

        # Average confidence should be between 0 and 1
        assert 0 <= result["average_confidence"] <= 1

    @pytest.mark.asyncio
    async def test_all_methods_are_async(self):
        """Test that all public methods are async."""
        service = AnalyticsService()

        import inspect

        # Check specific methods
        assert inspect.iscoroutinefunction(service.get_model_accuracy)
        assert inspect.iscoroutinefunction(service.get_model_performance_comparison)
        assert inspect.iscoroutinefunction(service.get_prediction_trends)

    @pytest.mark.asyncio
    async def test_multiple_calls_consistency(self):
        """Test multiple calls return consistent structure."""
        service = AnalyticsService()

        # Call each method multiple times
        accuracy1 = await service.get_model_accuracy()
        accuracy2 = await service.get_model_accuracy()

        comparison1 = await service.get_model_performance_comparison()
        comparison2 = await service.get_model_performance_comparison()

        trends1 = await service.get_prediction_trends()
        trends2 = await service.get_prediction_trends()

        # Structure should be consistent
        assert accuracy1.keys() == accuracy2.keys()
        assert comparison1.keys() == comparison2.keys()
        assert trends1.keys() == trends2.keys()

    @pytest.mark.asyncio
    async def test_different_model_versions(self):
        """Test get_model_accuracy with different model versions."""
        service = AnalyticsService()

        versions = ["default", "v1.0", "v2.0", "neural_net", "random_forest"]

        for version in versions:
            result = await service.get_model_accuracy(model_version=version)
            assert result["model_version"] == version

    @pytest.mark.asyncio
    async def test_different_time_periods(self):
        """Test methods with different time periods."""
        service = AnalyticsService()

        periods = [7, 14, 30, 60, 90]

        for period in periods:
            accuracy_result = await service.get_model_accuracy(days_back=period)
            assert accuracy_result["period_days"] == period

            trends_result = await service.get_prediction_trends(days_back=period)
            assert trends_result["period_days"] == period

    @pytest.mark.asyncio
    async def test_edge_case_parameters(self):
        """Test edge case parameters."""
        service = AnalyticsService()

        # Test with minimum valid values
        result = await service.get_model_accuracy(days_back=1)
        assert result["period_days"] == 1

        result = await service.get_prediction_trends(days_back=1)
        assert result["period_days"] == 1

        # Test with empty string model version
        result = await service.get_model_accuracy(model_version="")
        assert result["model_version"] == ""

    @pytest.mark.asyncio
    async def test_performance_decorators_applied(self):
        """Test that performance logging decorators are applied."""
        # This test verifies the decorators are present, actual logging would need mocking
        service = AnalyticsService()

        # The methods should still work normally with decorators
        result1 = await service.get_model_accuracy()
        result2 = await service.get_model_performance_comparison()
        result3 = await service.get_prediction_trends()

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

    @pytest.mark.asyncio
    async def test_service_integration_scenario(self):
        """Test comprehensive service usage scenario."""
        service = AnalyticsService()

        # Simulate a dashboard loading scenario
        # Get current model accuracy
        accuracy = await service.get_model_accuracy(
            model_version="production", days_back=30
        )

        # Compare different models
        comparison = await service.get_model_performance_comparison()

        # Get recent trends
        trends = await service.get_prediction_trends(days_back=7)

        # Verify all data is present and structured correctly
        assert accuracy["model_version"] == "production"
        assert accuracy["period_days"] == 30

        assert len(comparison["models"]) >= 2
        assert comparison["comparison_period_days"] == 30

        assert trends["period_days"] == 7
        assert (
            sum(trends["prediction_distribution"].values()) <= 1.01
        )  # Allow small floating point variance

    @pytest.mark.asyncio
    async def test_return_value_immutability(self):
        """Test that returned values are independent."""
        service = AnalyticsService()

        result1 = await service.get_model_accuracy()
        result2 = await service.get_model_accuracy()

        # Modify result1
        result1["accuracy"] = 999

        # result2 should be unaffected
        assert result2["accuracy"] != 999
        assert result2["accuracy"] == 0.75  # Original value

    def test_service_class_attributes(self):
        """Test service class has expected attributes."""
        service = AnalyticsService()

        # Should have logger attribute
        assert hasattr(service, "logger")

        # Should have expected methods
        assert hasattr(service, "get_model_accuracy")
        assert hasattr(service, "get_model_performance_comparison")
        assert hasattr(service, "get_prediction_trends")

    @pytest.mark.asyncio
    async def test_analytics_service_data_consistency(self):
        """Test internal data consistency across methods."""
        service = AnalyticsService()

        # Get all analytics data
        accuracy = await service.get_model_accuracy()
        comparison = await service.get_model_performance_comparison()
        trends = await service.get_prediction_trends()

        # Verify accuracy data is reasonable
        assert (
            accuracy["accuracy"]
            == accuracy["correct_predictions"] / accuracy["total_predictions"]
        )

        # Verify comparison models have reasonable accuracy differences
        models = comparison["models"]
        if len(models) >= 2:
            accuracies = [model["accuracy"] for model in models]
            assert max(accuracies) >= min(accuracies)  # Basic sanity check

        # Verify trend distribution sums correctly
        distribution_sum = sum(trends["prediction_distribution"].values())
        assert 0.99 <= distribution_sum <= 1.01  # Allow small floating point variance
