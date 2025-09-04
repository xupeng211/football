"""
Tests for model service.

Complete coverage tests for ModelService functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from football_predict_system.domain.models import Model
from football_predict_system.domain.services.model_service import (
    ModelService,
    get_available_models,
    get_model_service,
)


class TestModelService:
    """Test ModelService class."""

    def test_model_service_initialization(self):
        """Test ModelService initialization."""
        service = ModelService()

        assert service is not None
        assert hasattr(service, "logger")
        assert service.logger is not None

    @patch("football_predict_system.domain.services.model_service.get_logger")
    def test_model_service_logger_setup(self, mock_get_logger):
        """Test logger is properly set up."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        service = ModelService()

        assert service.logger is mock_logger
        mock_get_logger.assert_called_with(
            "football_predict_system.domain.services.model_service"
        )

    @pytest.mark.asyncio
    async def test_get_available_models_cache_hit(self):
        """Test get_available_models with cache hit."""
        service = ModelService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_data = [
            {
                "id": "12345678-1234-5678-9abc-123456789def",
                "name": "Test Model",
                "version": "1.0.0",
                "algorithm": "XGBoost",
                "description": "Test model",
                "accuracy": 0.75,
                "precision": 0.73,
                "recall": 0.77,
                "f1_score": 0.75,
                "roc_auc": 0.78,
                "log_loss": 0.45,
                "training_data_size": 10000,
                "created_at": "2024-01-01T00:00:00",
                "is_active": True,
            }
        ]
        mock_cache_manager.get.return_value = mock_cache_data

        with patch(
            "football_predict_system.domain.services.model_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            result = await service.get_available_models()

            # Should return a list of Model instances
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Model)
            assert result[0].name == "Test Model"
            assert result[0].version == "1.0.0"

            mock_cache_manager.get.assert_called_once_with("available_models", "models")
            mock_cache_manager.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_available_models_cache_miss(self):
        """Test get_available_models with cache miss."""
        service = ModelService()

        # Mock cache manager (cache miss)
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch(
            "football_predict_system.domain.services.model_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch.object(
                service, "_load_models_from_registry"
            ) as mock_load_models:
                # Mock models from registry
                mock_model = MagicMock()
                mock_model.dict.return_value = {"id": "test", "name": "Test Model"}
                mock_load_models.return_value = [mock_model]

                result = await service.get_available_models()

                # Should load from registry and cache
                assert result == [mock_model]
                mock_cache_manager.get.assert_called_once_with(
                    "available_models", "models"
                )
                mock_load_models.assert_called_once()
                mock_cache_manager.set.assert_called_once_with(
                    "available_models",
                    [{"id": "test", "name": "Test Model"}],
                    1800,
                    "models",
                )

    @pytest.mark.asyncio
    async def test_get_model_default_version(self):
        """Test get_model with default version."""
        service = ModelService()

        # Mock available models
        mock_model1 = MagicMock()
        mock_model1.is_active = False
        mock_model1.version = "1.0.0"

        mock_model2 = MagicMock()
        mock_model2.is_active = True
        mock_model2.version = "2.0.0"

        mock_models = [mock_model1, mock_model2]

        with patch.object(service, "get_available_models") as mock_get_models:
            mock_get_models.return_value = mock_models

            # Test with None version (default)
            result = await service.get_model(None)
            assert result is mock_model2  # First active model

            # Test with "default" version
            result = await service.get_model("default")
            assert result is mock_model2  # First active model

    @pytest.mark.asyncio
    async def test_get_model_specific_version(self):
        """Test get_model with specific version."""
        service = ModelService()

        mock_model1 = MagicMock()
        mock_model1.version = "1.0.0"
        mock_model1.is_active = True

        mock_model2 = MagicMock()
        mock_model2.version = "2.0.0"
        mock_model2.is_active = True

        mock_models = [mock_model1, mock_model2]

        with patch.object(service, "get_available_models") as mock_get_models:
            mock_get_models.return_value = mock_models

            result = await service.get_model("2.0.0")
            assert result is mock_model2

    @pytest.mark.asyncio
    async def test_get_model_not_found(self):
        """Test get_model with non-existent version."""
        service = ModelService()

        mock_model = MagicMock()
        mock_model.version = "1.0.0"
        mock_model.is_active = True

        with patch.object(service, "get_available_models") as mock_get_models:
            mock_get_models.return_value = [mock_model]

            result = await service.get_model("3.0.0")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_model_no_active_models(self):
        """Test get_model when no active models available."""
        service = ModelService()

        mock_model = MagicMock()
        mock_model.is_active = False
        mock_model.version = "1.0.0"

        with patch.object(service, "get_available_models") as mock_get_models:
            mock_get_models.return_value = [mock_model]

            result = await service.get_model()
            assert result is None

    @pytest.mark.asyncio
    async def test_get_model_metadata_with_id(self):
        """Test get_model_metadata with specific model ID."""
        service = ModelService()

        test_id = UUID("12345678-1234-5678-9abc-123456789def")

        result = await service.get_model_metadata(test_id)

        assert isinstance(result, dict)
        assert result["model_id"] == str(test_id)
        assert "features" in result
        assert "training_data_size" in result
        assert "last_updated" in result
        assert result["features"] == ["team_strength", "recent_form", "head_to_head"]
        assert result["training_data_size"] == 10000

    @pytest.mark.asyncio
    async def test_get_model_metadata_without_id(self):
        """Test get_model_metadata without model ID."""
        service = ModelService()

        result = await service.get_model_metadata()

        assert result["model_id"] == "default"
        assert result["features"] == ["team_strength", "recent_form", "head_to_head"]

    @pytest.mark.asyncio
    async def test_load_models_from_registry(self):
        """Test _load_models_from_registry returns expected models."""
        service = ModelService()

        models = await service._load_models_from_registry()

        assert isinstance(models, list)
        assert len(models) == 2

        # Check first model
        model1 = models[0]
        assert isinstance(model1, Model)
        assert model1.name == "Default XGBoost Model"
        assert model1.version == "1.0.0"
        assert model1.algorithm == "XGBoost"
        assert model1.accuracy == 0.75
        assert model1.is_active is True

        # Check second model
        model2 = models[1]
        assert isinstance(model2, Model)
        assert model2.name == "Neural Network v2"
        assert model2.version == "2.1.0"
        assert model2.algorithm == "Neural Network"
        assert model2.accuracy == 0.82
        assert model2.is_active is True

    @pytest.mark.asyncio
    async def test_load_models_from_registry_uuids(self):
        """Test _load_models_from_registry creates proper UUIDs."""
        service = ModelService()

        models = await service._load_models_from_registry()

        # Check UUIDs are properly set
        assert models[0].id == UUID("12345678-1234-5678-9abc-123456789def")
        assert models[1].id == UUID("87654321-4321-8765-cba9-fedcba987654")

    @pytest.mark.asyncio
    async def test_evaluate_model_performance_default_days(self):
        """Test evaluate_model_performance with default days."""
        service = ModelService()

        test_id = UUID("12345678-1234-5678-9abc-123456789def")

        result = await service.evaluate_model_performance(test_id)

        assert isinstance(result, dict)
        assert result["model_id"] == str(test_id)
        assert result["accuracy"] == 0.75
        assert result["precision"] == 0.73
        assert result["recall"] == 0.77
        assert result["f1_score"] == 0.75
        assert result["total_predictions"] == 100
        assert result["correct_predictions"] == 75
        assert result["period_days"] == 30  # Default value

    @pytest.mark.asyncio
    async def test_evaluate_model_performance_custom_days(self):
        """Test evaluate_model_performance with custom days."""
        service = ModelService()

        test_id = UUID("12345678-1234-5678-9abc-123456789def")

        result = await service.evaluate_model_performance(test_id, days_back=7)

        assert result["period_days"] == 7

    @pytest.mark.asyncio
    async def test_performance_decorators_present(self):
        """Test that performance logging decorators are applied."""
        service = ModelService()

        # Mock cache manager to avoid actual calls
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None

        with patch(
            "football_predict_system.domain.services.model_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            with patch.object(
                service, "_load_models_from_registry"
            ) as mock_load_models:
                mock_load_models.return_value = []

                # Method should execute without errors (decorator works)
                result = await service.get_available_models()
                assert result == []

    def test_service_class_attributes(self):
        """Test ModelService has expected attributes."""
        service = ModelService()

        assert hasattr(service, "logger")
        assert hasattr(service, "get_available_models")
        assert hasattr(service, "get_model")
        assert hasattr(service, "get_model_metadata")
        assert hasattr(service, "_load_models_from_registry")
        assert hasattr(service, "evaluate_model_performance")

    @pytest.mark.asyncio
    async def test_all_methods_are_async(self):
        """Test that all public methods are async."""
        service = ModelService()

        import inspect

        assert inspect.iscoroutinefunction(service.get_available_models)
        assert inspect.iscoroutinefunction(service.get_model)
        assert inspect.iscoroutinefunction(service.get_model_metadata)
        assert inspect.iscoroutinefunction(service._load_models_from_registry)
        assert inspect.iscoroutinefunction(service.evaluate_model_performance)


class TestGlobalModelService:
    """Test global model service functions."""

    def setup_method(self):
        """Reset global service before each test."""
        import football_predict_system.domain.services.model_service as module

        module._model_service = None

    def test_get_model_service_singleton(self):
        """Test get_model_service returns singleton instance."""
        service1 = get_model_service()
        service2 = get_model_service()

        assert service1 is service2
        assert isinstance(service1, ModelService)

    def test_get_model_service_creates_instance(self):
        """Test get_model_service creates new instance when None."""
        # Should create new instance
        service = get_model_service()
        assert service is not None
        assert isinstance(service, ModelService)

    def test_get_model_service_global_state(self):
        """Test global service state management."""
        import football_predict_system.domain.services.model_service as module

        # Initially None
        assert module._model_service is None

        # After call, should be set
        service = get_model_service()
        assert module._model_service is service

    @pytest.mark.asyncio
    async def test_get_available_models_convenience_function(self):
        """Test get_available_models convenience function."""
        mock_service = MagicMock()
        mock_models = [MagicMock()]
        mock_service.get_available_models = AsyncMock(return_value=mock_models)

        with patch(
            "football_predict_system.domain.services.model_service.get_model_service"
        ) as mock_get_service:
            mock_get_service.return_value = mock_service

            result = await get_available_models()

            assert result is mock_models
            mock_get_service.assert_called_once()
            mock_service.get_available_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_convenience_function_is_async(self):
        """Test that convenience function is async."""
        import inspect

        assert inspect.iscoroutinefunction(get_available_models)


class TestModelServiceIntegration:
    """Integration tests for ModelService."""

    def setup_method(self):
        """Reset global service before each test."""
        import football_predict_system.domain.services.model_service as module

        module._model_service = None

    @pytest.mark.asyncio
    async def test_full_model_workflow(self):
        """Test complete model workflow."""
        service = ModelService()

        # Mock cache manager
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None  # Cache miss

        with patch(
            "football_predict_system.domain.services.model_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            # Get available models (should load from registry)
            models = await service.get_available_models()
            assert len(models) == 2

            # Get default model
            default_model = await service.get_model()
            assert default_model is not None
            assert default_model.is_active is True

            # Get specific model
            specific_model = await service.get_model("2.1.0")
            assert specific_model is not None
            assert specific_model.version == "2.1.0"

            # Get model metadata
            metadata = await service.get_model_metadata(default_model.id)
            assert metadata["model_id"] == str(default_model.id)

            # Evaluate performance
            performance = await service.evaluate_model_performance(default_model.id)
            assert performance["model_id"] == str(default_model.id)

    @pytest.mark.asyncio
    async def test_cache_behavior_integration(self):
        """Test caching behavior in integration scenario."""
        service = ModelService()

        mock_cache_manager = AsyncMock()
        # Create complete model data for cache
        cached_model_data = [
            {
                "id": "12345678-1234-5678-9abc-123456789def",
                "name": "Cached Model",
                "version": "1.0.0",
                "algorithm": "XGBoost",
                "description": "Cached test model",
                "accuracy": 0.80,
                "precision": 0.78,
                "recall": 0.82,
                "f1_score": 0.80,
                "roc_auc": 0.83,
                "log_loss": 0.42,
                "training_data_size": 8000,
                "created_at": "2024-01-01T00:00:00",
                "is_active": True,
            }
        ]

        mock_cache_manager.get.side_effect = [None, cached_model_data]

        with patch(
            "football_predict_system.domain.services.model_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache_manager

            # First call - cache miss, should load from registry
            models1 = await service.get_available_models()
            assert mock_cache_manager.set.call_count == 1
            assert len(models1) == 2  # From registry

            # Second call - cache hit, should use cached data
            models2 = await service.get_available_models()
            assert len(models2) == 1  # From cache
            assert models2[0].name == "Cached Model"

    @pytest.mark.asyncio
    async def test_global_and_instance_integration(self):
        """Test integration between global functions and instance methods."""
        # Use convenience function
        models = await get_available_models()
        assert len(models) == 2

        # Use global service directly
        service = get_model_service()
        model = await service.get_model("1.0.0")
        assert model is not None
        assert model.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_model_data_consistency(self):
        """Test that model data is consistent across calls."""
        service = ModelService()

        models = await service._load_models_from_registry()

        # Verify model data structure
        for model in models:
            assert hasattr(model, "id")
            assert hasattr(model, "name")
            assert hasattr(model, "version")
            assert hasattr(model, "algorithm")
            assert hasattr(model, "accuracy")
            assert hasattr(model, "precision")
            assert hasattr(model, "recall")
            assert hasattr(model, "f1_score")
            assert hasattr(model, "roc_auc")
            assert hasattr(model, "log_loss")
            assert hasattr(model, "training_data_size")
            assert hasattr(model, "created_at")
            assert hasattr(model, "is_active")

            # Verify data types
            assert isinstance(model.id, UUID)
            assert isinstance(model.accuracy, float)
            assert isinstance(model.training_data_size, int)
            assert isinstance(model.created_at, datetime)
            assert isinstance(model.is_active, bool)

    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self):
        """Test various error handling scenarios."""
        service = ModelService()

        # Test with empty model list
        with patch.object(service, "_load_models_from_registry") as mock_load:
            mock_load.return_value = []

            models = await service.get_available_models()
            assert models == []

            # Should handle no models gracefully
            model = await service.get_model()
            assert model is None
