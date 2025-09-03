"""
Domain services for the football prediction system.

This module contains the business logic services that orchestrate
domain operations and enforce business rules.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ..core.cache import get_cache_manager
from ..core.exceptions import (
    InsufficientDataError,
    ModelNotFoundError,
    NotFoundError,
    PredictionError,
)
from ..core.logging import get_logger, log_performance
from .models import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    Match,
    MatchStatus,
    Model,
    Prediction,
    PredictionRequest,
    PredictionResponse,
    Team,
)

logger = get_logger(__name__)


class PredictionService:
    """Service for generating match predictions."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
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
                from .models import MatchResult, Prediction, PredictionConfidence

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
                    prediction_date=datetime.fromisoformat(
                        prediction_data["prediction_date"]
                    )
                    if isinstance(prediction_data["prediction_date"], str)
                    else prediction_data["prediction_date"],
                )

                return PredictionResponse(
                    prediction=prediction,
                    match_info=cached_prediction["match_info"],
                    model_info=cached_prediction["model_info"],
                )
            except (KeyError, ValueError, TypeError) as e:
                self.logger.warning(
                    f"Failed to reconstruct cached prediction: {e}, generating new prediction"
                )
                # Continue to generate new prediction if cache reconstruction fails

        # Get match data
        match = await self._get_match(request.match_id)
        if not match:
            raise NotFoundError("match", str(request.match_id))

        # Get model
        model = await self._get_model(request.model_version)
        if not model:
            raise ModelNotFoundError(request.model_version or "default")

        # Generate features
        features = await self._extract_features(match)
        if not features:
            raise InsufficientDataError("No features available for prediction")

        # Make prediction
        try:
            prediction = await self._predict_with_model(model, features, match)

            # Create response
            response = PredictionResponse(
                prediction=prediction,
                match_info={
                    "home_team": str(match.home_team_id),
                    "away_team": str(match.away_team_id),
                    "scheduled_date": match.scheduled_date,
                    "competition": match.competition,
                },
                model_info={
                    "name": model.name,
                    "version": model.version,
                    "accuracy": model.accuracy or 0.0,
                },
            )

            # Cache the result
            await cache_manager.set(cache_key, response.dict(), 3600, "predictions")

            self.logger.info(
                "Prediction generated successfully",
                match_id=request.match_id,
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
            raise PredictionError(f"Failed to generate prediction: {e!s}")

    @log_performance("generate_batch_predictions")
    async def generate_batch_predictions(
        self, request: BatchPredictionRequest
    ) -> BatchPredictionResponse:
        """Generate predictions for multiple matches."""
        predictions = []
        errors = []

        # Process predictions concurrently
        tasks = []
        for match_id in request.match_ids:
            pred_request = PredictionRequest(
                match_id=match_id,
                model_version=request.model_version,
                include_probabilities=request.include_probabilities,
                include_expected_scores=request.include_expected_scores,
            )
            tasks.append(self._safe_generate_prediction(pred_request))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(
                    {
                        "match_id": str(request.match_ids[i]),
                        "error": str(result),
                    }
                )
            elif result is not None and isinstance(result, PredictionResponse):
                predictions.append(result)

        return BatchPredictionResponse(
            predictions=predictions,
            total_count=len(request.match_ids),
            successful_predictions=len(predictions),
            failed_predictions=len(errors),
            errors=errors,
        )

    async def _safe_generate_prediction(
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

    async def _get_match(self, match_id: UUID) -> Match | None:
        """Get match data from database."""
        return await self._data_service.get_match_data(match_id)

    async def _get_model(self, model_version: str | None) -> Model | None:
        """Get model from registry."""
        if model_version:
            return await self._model_service.get_model_by_version(model_version)
        else:
            return await self._model_service.get_default_model()

    async def _extract_features(self, match: Match) -> dict[str, Any] | None:
        """Extract features for prediction."""
        # This would integrate with your feature extraction pipeline
        # Placeholder implementation
        return {}

    async def _predict_with_model(
        self, model: Model, features: dict[str, Any], match: Match
    ) -> Prediction:
        """Make prediction using the model."""
        # This would integrate with your ML model
        # Placeholder implementation
        from .models import MatchResult, PredictionConfidence

        return Prediction(
            match_id=match.id,
            model_version=model.version,
            predicted_result=MatchResult.HOME_WIN,
            home_win_probability=0.5,
            draw_probability=0.3,
            away_win_probability=0.2,
            confidence_level=PredictionConfidence.MEDIUM,
            confidence_score=0.75,
            expected_home_score=0.0,
            expected_away_score=0.0,
            features_used=list(features.keys()),
            model_accuracy=model.accuracy,
        )


class ModelService:
    """Service for handling ML model operations."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    @log_performance("get_available_models")
    async def get_available_models(self) -> list[Model]:
        """Get list of available models."""
        cache_manager = await get_cache_manager()

        # Check cache first
        cached_models = await cache_manager.get("available_models", "models")
        if cached_models:
            return [Model(**model_data) for model_data in cached_models]

        # Get from database/registry
        models = await self._load_models_from_registry()

        # Cache the result
        models_data = [model.dict() for model in models]
        await cache_manager.set(
            "available_models", models_data, 1800, "models"
        )  # 30 minutes

        return models

    @log_performance("get_model_by_version")
    async def get_model_by_version(self, version: str) -> Model | None:
        """Get specific model by version."""
        models = await self.get_available_models()
        return next((model for model in models if model.version == version), None)

    @log_performance("get_default_model")
    async def get_default_model(self) -> Model | None:
        """Get the default/production model."""
        models = await self.get_available_models()
        production_models = [model for model in models if model.is_production]

        if production_models:
            # Return the most recent production model
            latest_model = max(production_models, key=lambda m: m.created_at)
            return latest_model if isinstance(latest_model, Model) else None

        # Fallback to most recent active model
        active_models = [model for model in models if model.is_active]
        if active_models:
            latest_active = max(active_models, key=lambda m: m.created_at)
            return latest_active if isinstance(latest_active, Model) else None

        return None

    async def _load_models_from_registry(self) -> list[Model]:
        """Load models from registry."""
        # Mock implementation for testing
        from uuid import uuid4

        mock_model = Model(
            id=uuid4(),
            name="MockModel",
            version="1.0.0",
            algorithm="RandomForest",
            description="Mock model for testing",
            accuracy=0.85,
            precision=0.83,
            recall=0.87,
            f1_score=0.85,
            roc_auc=0.92,
            log_loss=0.35,
            training_data_size=1000,
        )

        return [mock_model]


class DataService:
    """Service for handling data operations."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    @log_performance("get_match_data")
    async def get_match_data(self, match_id: UUID) -> Match | None:
        """Get match data with caching."""
        cache_manager = await get_cache_manager()

        # Check cache first
        cache_key = str(match_id)
        cached_match = await cache_manager.get(cache_key, "matches")
        if cached_match:
            return Match(**cached_match)

        # Get from database
        match = await self._load_match_from_db(match_id)
        if match:
            # Cache the result
            await cache_manager.set(
                cache_key, match.dict(), 1800, "matches"
            )  # 30 minutes

        return match

    @log_performance("get_team_data")
    async def get_team_data(self, team_id: UUID) -> Team | None:
        """Get team data with caching."""
        cache_manager = await get_cache_manager()

        # Check cache first
        cache_key = str(team_id)
        cached_team = await cache_manager.get(cache_key, "teams")
        if cached_team:
            return Team(**cached_team)

        # Get from database
        team = await self._load_team_from_db(team_id)
        if team:
            # Cache the result
            await cache_manager.set(cache_key, team.dict(), 3600, "teams")  # 1 hour

        return team

    @log_performance("get_upcoming_matches")
    async def get_upcoming_matches(self, days_ahead: int = 7) -> list[Match]:
        """Get upcoming matches."""
        cache_key = f"upcoming_{days_ahead}d"
        cache_manager = await get_cache_manager()

        # Check cache first
        cached_matches = await cache_manager.get(cache_key, "matches")
        if cached_matches:
            return [Match(**match_data) for match_data in cached_matches]

        # Get from database
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        matches = await self._load_upcoming_matches_from_db(end_date)

        # Cache the result
        matches_data = [match.dict() for match in matches]
        await cache_manager.set(cache_key, matches_data, 900, "matches")  # 15 minutes

        return matches

    async def _load_match_from_db(self, match_id: UUID) -> Match | None:
        """Load match from database."""
        # Mock implementation for testing
        from datetime import datetime, timedelta
        from uuid import uuid4

        return Match(
            id=match_id,
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            scheduled_date=datetime.utcnow() + timedelta(days=7),
            competition="Premier League",
            season="2024-25",
            matchday=1,
            status=MatchStatus.SCHEDULED,
            home_score=None,
            away_score=None,
            # 添加所有必需的统计参数
            home_possession=None,
            away_possession=None,
            home_shots=None,
            away_shots=None,
            home_shots_on_target=None,
            away_shots_on_target=None,
            home_odds=None,
            draw_odds=None,
            away_odds=None,
        )

    async def _load_team_from_db(self, team_id: UUID) -> Team | None:
        """Load team from database."""
        # Mock implementation for testing
        return Team(
            id=team_id,
            name="Mock Team",
            short_name="MOC",
            country="England",
            founded_year=1900,
            venue="Mock Stadium",  # 使用venue而不是stadium
        )

    async def _load_upcoming_matches_from_db(self, end_date: datetime) -> list[Match]:
        """Load upcoming matches from database."""
        # Mock implementation for testing
        return []


class AnalyticsService:
    """Service for analytics and reporting."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    @log_performance("get_prediction_accuracy")
    async def get_prediction_accuracy(
        self, model_version: str | None = None, days_back: int = 30
    ) -> dict[str, Any]:
        """Calculate prediction accuracy over time period."""
        # This would analyze historical predictions vs actual results
        # Placeholder implementation
        return {
            "accuracy": 0.75,
            "total_predictions": 100,
            "correct_predictions": 75,
            "period_days": days_back,
            "model_version": model_version,
        }

    @log_performance("get_model_performance_comparison")
    async def get_model_performance_comparison(self) -> dict[str, Any]:
        """Compare performance of different models."""
        # This would compare multiple models
        # Placeholder implementation
        return {
            "models": [],
            "comparison_period": "30_days",
            "metrics": ["accuracy", "precision", "recall", "f1_score"],
        }


# Global service instances
prediction_service = PredictionService()
model_service = ModelService()
data_service = DataService()
analytics_service = AnalyticsService()
