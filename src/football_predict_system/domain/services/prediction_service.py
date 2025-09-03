"""
Prediction service for generating match predictions.

This service handles:
- Match prediction generation
- Prediction caching
- Batch prediction processing
- Prediction validation
"""

import asyncio
from datetime import datetime

from ...core.cache import get_cache_manager
from ...core.exceptions import (
    InsufficientDataError,
    ModelNotFoundError,
    PredictionError,
)
from ...core.logging import get_logger, log_performance
from ..models import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    MatchResult,
    Prediction,
    PredictionConfidence,
    PredictionRequest,
    PredictionResponse,
)

logger = get_logger(__name__)


class PredictionService:
    """Service for generating match predictions."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        # Import here to avoid circular imports
        from .data_service import DataService
        from .model_service import ModelService

        self._model_service = ModelService()
        self._data_service = DataService()

    @log_performance("generate_prediction")
    async def generate_prediction(
        self, request: PredictionRequest
    ) -> PredictionResponse:
        """Generate a prediction for a match."""
        cache_manager = await get_cache_manager()

        # Check cache first
        cache_key = f"{request.match_id}:{request.model_version or 'default'}"
        cached_prediction = await cache_manager.get(cache_key, "predictions")

        if cached_prediction:
            self.logger.info("Prediction served from cache", match_id=request.match_id)
            try:
                # Safely reconstruct the prediction object
                prediction_data = cached_prediction["prediction"]

                prediction = Prediction(
                    id=prediction_data["id"],
                    match_id=prediction_data["match_id"],
                    model_version=prediction_data["model_version"],
                    predicted_result=MatchResult(prediction_data["predicted_result"]),
                    home_win_probability=prediction_data["home_win_probability"],
                    draw_probability=prediction_data["draw_probability"],
                    away_win_probability=prediction_data["away_win_probability"],
                    confidence_level=PredictionConfidence(
                        prediction_data["confidence_level"]
                    ),
                    confidence_score=prediction_data["confidence_score"],
                    expected_home_score=prediction_data.get("expected_home_score"),
                    expected_away_score=prediction_data.get("expected_away_score"),
                    features_used=prediction_data.get("features_used", []),
                    model_accuracy=prediction_data.get("model_accuracy"),
                    created_at=datetime.fromisoformat(prediction_data["created_at"])
                    if isinstance(prediction_data["created_at"], str)
                    else prediction_data["created_at"],
                )

                response = PredictionResponse(
                    match_id=request.match_id,
                    prediction=prediction,
                    predicted_result=prediction.predicted_result,
                    confidence=prediction.confidence_score,
                )

                return response

            except (KeyError, ValueError, TypeError) as e:
                self.logger.warning(
                    "Cached prediction corrupted, regenerating",
                    match_id=request.match_id,
                    error=str(e),
                )
                # Continue to generate new prediction

        # Generate new prediction
        try:
            # Get match data
            match = await self._data_service.get_match_by_id(request.match_id)
            if not match:
                raise InsufficientDataError(f"Match {request.match_id} not found")

            # Get model
            model = await self._model_service.get_model(
                request.model_version or "default"
            )
            if not model:
                raise ModelNotFoundError(f"Model {request.model_version} not available")

            # Generate prediction using model
            prediction = await self._generate_prediction_internal(match, model)

            # Cache the prediction
            cache_data = {
                "prediction": prediction.model_dump(mode="json"),
                "cached_at": datetime.utcnow().isoformat(),
            }
            await cache_manager.set(cache_key, cache_data, 3600, "predictions")

            response = PredictionResponse(
                match_id=request.match_id,
                prediction=prediction,
                predicted_result=prediction.predicted_result,
                confidence=prediction.confidence_score,
            )

            return response

        except (InsufficientDataError, ModelNotFoundError, PredictionError) as e:
            self.logger.error(
                "Prediction generation failed",
                match_id=request.match_id,
                error=str(e),
            )
            raise

    async def generate_prediction_safely(
        self, request: PredictionRequest
    ) -> PredictionResponse | None:
        """Safely generate a prediction, handling exceptions."""
        try:
            result = await self.generate_prediction(request)
            return result if isinstance(result, PredictionResponse) else None
        except (
            InsufficientDataError,
            ModelNotFoundError,
            PredictionError,
            ValueError,
        ) as e:
            self.logger.warning(
                "Prediction failed for match",
                match_id=request.match_id,
                error=str(e),
            )
            return None

    @log_performance("generate_batch_predictions")
    async def generate_batch_predictions(
        self, request: BatchPredictionRequest
    ) -> BatchPredictionResponse:
        """Generate predictions for multiple matches."""
        self.logger.info(
            "Starting batch prediction",
            match_count=len(request.match_ids),
            model_version=request.model_version,
        )

        # Create individual prediction requests
        prediction_requests = [
            PredictionRequest(
                match_id=match_id,
                model_version=request.model_version,
                include_features=request.include_features,
            )
            for match_id in request.match_ids
        ]

        # Process predictions concurrently with controlled concurrency
        semaphore = asyncio.Semaphore(5)  # Limit concurrent predictions

        async def predict_with_semaphore(req: PredictionRequest):
            async with semaphore:
                return await self.generate_prediction_safely(req)

        predictions = await asyncio.gather(
            *[predict_with_semaphore(req) for req in prediction_requests],
            return_exceptions=True,
        )

        # Filter successful predictions
        successful_predictions = [
            pred for pred in predictions if isinstance(pred, PredictionResponse)
        ]

        # Count failures
        failed_count = len(predictions) - len(successful_predictions)

        if failed_count > 0:
            self.logger.warning(
                "Some batch predictions failed",
                total_requested=len(request.match_ids),
                successful=len(successful_predictions),
                failed=failed_count,
            )

        return BatchPredictionResponse(
            predictions=successful_predictions,
            total_requested=len(request.match_ids),
            successful_count=len(successful_predictions),
            failed_count=failed_count,
        )

    async def _generate_prediction_internal(self, match, model) -> Prediction:
        """Internal prediction generation logic."""
        # Placeholder implementation - replace with actual ML logic
        import uuid
        from random import uniform

        return Prediction(
            id=str(uuid.uuid4()),
            match_id=match.id,
            model_version=model.version,
            predicted_result=MatchResult.HOME_WIN,
            home_win_probability=uniform(0.3, 0.7),  # nosec B311
            draw_probability=uniform(0.2, 0.4),  # nosec B311
            away_win_probability=uniform(0.1, 0.5),  # nosec B311
            confidence_level=PredictionConfidence.MEDIUM,
            confidence_score=uniform(0.6, 0.9),  # nosec B311
            features_used=["team_form", "head_to_head", "home_advantage"],
            model_accuracy=model.accuracy if hasattr(model, "accuracy") else 0.75,
            created_at=datetime.utcnow(),
        )
