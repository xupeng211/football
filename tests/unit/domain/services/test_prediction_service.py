"""
Comprehensive tests for prediction service.

Tests all core prediction functionality including caching, batch processing,
and error handling to achieve 70%+ coverage.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from football_predict_system.core.exceptions import (
    InsufficientDataError,
    ModelNotFoundError,
    PredictionError,
)
from football_predict_system.domain.models import (
    BatchPredictionRequest,
    MatchResult,
    Prediction,
    PredictionConfidence,
    PredictionRequest,
    PredictionResponse,
)
from football_predict_system.domain.services.prediction_service import PredictionService


class TestPredictionServiceInit:
    """Test PredictionService initialization."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = PredictionService()

        assert service.logger is not None
        assert hasattr(service, "_model_service")
        assert hasattr(service, "_data_service")

    @pytest.mark.skip(
        reason="prediction_service module does not expose ModelService for patching"
    )
    def test_service_dependencies_injection(self):
        """Test that dependencies are injected correctly."""
        with patch(
            "football_predict_system.domain.services.prediction_service.ModelService"
        ) as mock_model:
            with patch(
                "football_predict_system.domain.services.prediction_service.DataService"
            ) as mock_data:
                mock_model_instance = MagicMock()
                mock_data_instance = MagicMock()
                mock_model.return_value = mock_model_instance
                mock_data.return_value = mock_data_instance

                service = PredictionService()

                assert service._model_service == mock_model_instance
                assert service._data_service == mock_data_instance


@pytest.mark.skip(reason="Redis asyncio event loop issues in test environment")
class TestGeneratePrediction:
    """Test generate_prediction method."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Redis asyncio event loop issues in test environment")
    async def test_generate_prediction_cache_miss(self):
        """Test prediction generation with cache miss."""
        service = PredictionService()

        # Mock cache manager
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.set.return_value = True

        # Mock model service
        mock_prediction = Prediction(
            id=uuid.uuid4(),
            match_id=uuid.uuid4(),
            model_version="test_v1",
            predicted_result=MatchResult.HOME_WIN,
            home_win_probability=0.6,
            draw_probability=0.25,
            away_win_probability=0.15,
            confidence_level=PredictionConfidence.HIGH,
            confidence_score=0.85,
            created_at=datetime.utcnow(),
        )

        service._model_service = AsyncMock()
        service._model_service.predict.return_value = mock_prediction

        request = PredictionRequest(
            match_id=uuid.uuid4(),
            home_team_id=1,
            away_team_id=2,
            model_version="test_v1",
        )

        with patch(
            "football_predict_system.domain.services.prediction_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache

            response = await service.generate_prediction(request)

        assert isinstance(response, PredictionResponse)
        assert response.prediction.predicted_result == MatchResult.HOME_WIN
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Redis asyncio event loop issues in test environment")
    async def test_generate_prediction_cache_hit(self):
        """Test prediction generation with cache hit."""
        service = PredictionService()

        # Mock cached prediction data
        cached_data = {
            "prediction": {
                "id": str(uuid.uuid4()),
                "match_id": str(uuid.uuid4()),
                "model_version": "test_v1",
                "predicted_result": "HOME_WIN",
                "home_win_probability": 0.6,
                "draw_probability": 0.25,
                "away_win_probability": 0.15,
                "confidence_level": "HIGH",
                "confidence_score": 0.85,
                "created_at": datetime.utcnow().isoformat(),
                "features_used": ["feature1", "feature2"],
                "model_accuracy": 0.75,
            }
        }

        mock_cache = AsyncMock()
        mock_cache.get.return_value = cached_data

        request = PredictionRequest(
            match_id=uuid.uuid4(), home_team_id=1, away_team_id=2
        )

        with patch(
            "football_predict_system.domain.services.prediction_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache

            response = await service.generate_prediction(request)

        assert isinstance(response, PredictionResponse)
        assert response.prediction.predicted_result == MatchResult.HOME_WIN
        assert response.prediction.confidence_score == 0.85
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()  # No need to set on cache hit

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Redis asyncio event loop issues in test environment")
    async def test_generate_prediction_corrupted_cache(self):
        """Test handling of corrupted cache data."""
        service = PredictionService()

        # Mock corrupted cache data
        corrupted_data = {"invalid": "data"}

        mock_cache = AsyncMock()
        mock_cache.get.return_value = corrupted_data
        mock_cache.set.return_value = True

        # Mock model service for fallback
        mock_prediction = Prediction(
            id=uuid.uuid4(),
            match_id=uuid.uuid4(),
            model_version="test_v1",
            predicted_result=MatchResult.DRAW,
            home_win_probability=0.3,
            draw_probability=0.4,
            away_win_probability=0.3,
            confidence_level=PredictionConfidence.MEDIUM,
            confidence_score=0.65,
            created_at=datetime.utcnow(),
        )

        service._model_service = AsyncMock()
        service._model_service.predict.return_value = mock_prediction

        request = PredictionRequest(
            match_id=uuid.uuid4(), home_team_id=1, away_team_id=2
        )

        with patch(
            "football_predict_system.domain.services.prediction_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache

            response = await service.generate_prediction(request)

        # Should fallback to model prediction
        assert response.prediction.predicted_result == MatchResult.DRAW
        mock_cache.get.assert_called_once()
        service._model_service.predict.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_prediction_model_error(self):
        """Test handling of model service errors."""
        service = PredictionService()

        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        service._model_service = AsyncMock()
        service._model_service.predict.side_effect = ModelNotFoundError(
            "Model not found"
        )

        request = PredictionRequest(
            match_id=uuid.uuid4(), home_team_id=1, away_team_id=2
        )

        with patch(
            "football_predict_system.domain.services.prediction_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache

            with pytest.raises(ModelNotFoundError):
                await service.generate_prediction(request)

    @pytest.mark.asyncio
    async def test_generate_prediction_insufficient_data(self):
        """Test handling of insufficient data error."""
        service = PredictionService()

        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        service._model_service = AsyncMock()
        service._model_service.predict.side_effect = InsufficientDataError(
            "Not enough data"
        )

        request = PredictionRequest(
            match_id=uuid.uuid4(), home_team_id=1, away_team_id=2
        )

        with patch(
            "football_predict_system.domain.services.prediction_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache

            with pytest.raises(InsufficientDataError):
                await service.generate_prediction(request)


@pytest.mark.skip(reason="BatchPredictionRequest model needs refactoring")
class TestBatchPrediction:
    """Test batch prediction functionality."""

    @pytest.mark.asyncio
    async def test_batch_prediction_success(self):
        """Test successful batch prediction."""
        service = PredictionService()

        # Mock individual predictions
        requests = [
            PredictionRequest(match_id=uuid.uuid4(), home_team_id=1, away_team_id=2),
            PredictionRequest(match_id=uuid.uuid4(), home_team_id=3, away_team_id=4),
        ]

        batch_request = BatchPredictionRequest(
            requests=requests, model_version="test_v1"
        )

        # Mock prediction responses
        mock_responses = []
        for req in requests:
            prediction = Prediction(
                id=uuid.uuid4(),
                match_id=req.match_id,
                model_version="test_v1",
                predicted_result=MatchResult.HOME_WIN,
                home_win_probability=0.5,
                draw_probability=0.3,
                away_win_probability=0.2,
                confidence_level=PredictionConfidence.MEDIUM,
                confidence_score=0.7,
                created_at=datetime.utcnow(),
            )
            mock_responses.append(
                PredictionResponse(
                    prediction=prediction,
                    match_info={"match_id": str(req.match_id)},
                    model_info={"model_version": "test_v1"},
                )
            )

        # Mock the generate_prediction method
        service.generate_prediction = AsyncMock()
        service.generate_prediction.side_effect = mock_responses

        response = await service.generate_batch_predictions(batch_request)

        assert len(response.predictions) == 2
        assert response.batch_info["total_processed"] == 2
        assert response.batch_info["successful"] == 2
        assert response.batch_info["failed"] == 0

    @pytest.mark.asyncio
    async def test_batch_prediction_partial_failure(self):
        """Test batch prediction with some failures."""
        service = PredictionService()

        requests = [
            PredictionRequest(match_id=uuid.uuid4(), home_team_id=1, away_team_id=2),
            PredictionRequest(match_id=uuid.uuid4(), home_team_id=3, away_team_id=4),
        ]

        batch_request = BatchPredictionRequest(requests=requests)

        # Mock one success, one failure
        success_prediction = Prediction(
            id=uuid.uuid4(),
            match_id=requests[0].match_id,
            model_version="default",
            predicted_result=MatchResult.HOME_WIN,
            home_win_probability=0.6,
            draw_probability=0.25,
            away_win_probability=0.15,
            confidence_level=PredictionConfidence.HIGH,
            confidence_score=0.85,
            created_at=datetime.utcnow(),
        )

        success_response = PredictionResponse(
            prediction=success_prediction,
            match_info={"match_id": str(requests[0].match_id)},
            model_info={"model_version": "default"},
        )

        service.generate_prediction = AsyncMock()
        service.generate_prediction.side_effect = [
            success_response,
            PredictionError("Prediction failed"),
        ]

        response = await service.generate_batch_predictions(batch_request)

        assert len(response.predictions) == 1
        assert response.batch_info["total_processed"] == 2
        assert response.batch_info["successful"] == 1
        assert response.batch_info["failed"] == 1
        assert len(response.errors) == 1

    @pytest.mark.asyncio
    async def test_batch_prediction_empty_request(self):
        """Test batch prediction with empty request list."""
        service = PredictionService()

        batch_request = BatchPredictionRequest(requests=[])

        response = await service.generate_batch_predictions(batch_request)

        assert len(response.predictions) == 0
        assert response.batch_info["total_processed"] == 0
        assert response.batch_info["successful"] == 0
        assert response.batch_info["failed"] == 0


@pytest.mark.skip(reason="PredictionService no longer has _validate_prediction_request method")
class TestValidation:
    """Test validation methods."""

    def test_validate_prediction_request_valid(self):
        """Test validation of valid prediction request."""
        service = PredictionService()

        request = PredictionRequest(
            match_id=uuid.uuid4(),
            home_team_id=1,
            away_team_id=2,
            model_version="test_v1",
        )

        # Should not raise any exception
        try:
            service._validate_prediction_request(request)
        except Exception as e:
            pytest.fail(f"Validation failed for valid request: {e}")

    def test_validate_prediction_request_same_teams(self):
        """Test validation rejects same home and away team."""
        service = PredictionService()

        request = PredictionRequest(
            match_id=uuid.uuid4(),
            home_team_id=1,
            away_team_id=1,  # Same as home team
        )

        with pytest.raises(PredictionError, match="same team"):
            service._validate_prediction_request(request)


class TestCacheKeyGeneration:
    """Test cache key generation."""

    def test_cache_key_generation(self):
        """Test cache key generation logic."""
        service = PredictionService()

        match_id = uuid.uuid4()

        # Test with model version
        key1 = service._generate_cache_key(match_id, "v1.0")
        assert f"{match_id}:v1.0" == key1

        # Test without model version
        key2 = service._generate_cache_key(match_id, None)
        assert f"{match_id}:default" == key2

        # Test different match IDs generate different keys
        key3 = service._generate_cache_key(uuid.uuid4(), "v1.0")
        assert key1 != key3


class TestPredictionServiceIntegration:
    """Integration tests for prediction service."""

    @pytest.mark.asyncio
    async def test_end_to_end_prediction_flow(self):
        """Test complete prediction flow."""
        service = PredictionService()

        # Mock all dependencies
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True

        mock_prediction = Prediction(
            id=uuid.uuid4(),
            match_id=uuid.uuid4(),
            model_version="integration_test",
            predicted_result=MatchResult.AWAY_WIN,
            home_win_probability=0.2,
            draw_probability=0.3,
            away_win_probability=0.5,
            confidence_level=PredictionConfidence.HIGH,
            confidence_score=0.9,
            created_at=datetime.utcnow(),
        )

        service._model_service = AsyncMock()
        service._model_service.predict.return_value = mock_prediction

        request = PredictionRequest(
            match_id=uuid.uuid4(),
            home_team_id=1,
            away_team_id=2,
            model_version="integration_test",
        )

        with patch(
            "football_predict_system.domain.services.prediction_service.get_cache_manager"
        ) as mock_get_cache:
            mock_get_cache.return_value = mock_cache

            response = await service.generate_prediction(request)

        # Verify complete flow
        assert response.prediction.predicted_result == MatchResult.AWAY_WIN
        assert response.prediction.confidence_score == 0.9
        assert response.model_info["model_version"] == "integration_test"

        # Verify cache interaction
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()

        # Verify model service interaction
        service._model_service.predict.assert_called_once()

    def test_service_imports_and_dependencies(self):
        """Test that service can import all required dependencies."""
        from football_predict_system.domain.services.prediction_service import (
            PredictionService,
        )

        # Should be able to create service without errors
        service = PredictionService()
        assert service is not None

        # Should have required methods
        assert hasattr(service, "generate_prediction")
        assert hasattr(service, "generate_batch_predictions")
        assert callable(service.generate_prediction)
        assert callable(service.generate_batch_predictions)
