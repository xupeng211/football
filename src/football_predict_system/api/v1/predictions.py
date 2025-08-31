"""
Predictions API endpoints for v1.

This module provides REST API endpoints for football match predictions
with enhanced error handling, validation, and monitoring.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...core.exceptions import (
    BaseApplicationError,
    InsufficientDataError,
    ModelNotFoundError,
    PredictionError,
)
from ...core.logging import get_logger
from ...core.security import Permission, User, require_permission
from ...domain.models import BatchPredictionRequest, MatchResult, PredictionRequest
from ...domain.services import prediction_service

logger = get_logger(__name__)
router = APIRouter()


# Legacy request models for backward compatibility
class LegacySingleMatchRequest(BaseModel):
    """Legacy single match prediction request for backward compatibility."""

    home_team: str = Field(..., description="Home team name", examples=["Arsenal"])
    away_team: str = Field(..., description="Away team name", examples=["Chelsea"])
    match_date: date = Field(..., description="Match date", examples=["2025-08-30"])
    home_odds: float = Field(..., description="Home win odds", gt=1.0, examples=[2.1])
    draw_odds: float = Field(..., description="Draw odds", gt=1.0, examples=[3.3])
    away_odds: float = Field(..., description="Away win odds", gt=1.0, examples=[3.2])


class LegacyBatchMatchRequest(BaseModel):
    """Legacy batch match prediction request."""

    matches: List[LegacySingleMatchRequest] = Field(
        ..., description="List of matches", min_length=1, max_length=50
    )


class LegacyPredictionResponse(BaseModel):
    """Legacy prediction response for backward compatibility."""

    prediction_id: str = Field(..., description="Prediction ID")
    home_team: str = Field(..., description="Home team")
    away_team: str = Field(..., description="Away team")
    match_date: date = Field(..., description="Match date")
    predicted_outcome: str = Field(..., description="Predicted result")
    confidence: float = Field(..., description="Confidence score", ge=0, le=1)
    created_at: datetime = Field(..., description="Creation time")


class LegacyBatchPredictionResponse(BaseModel):
    """Legacy batch prediction response."""

    predictions: List[LegacyPredictionResponse] = Field(
        ..., description="Prediction results"
    )
    total_matches: int = Field(..., description="Total number of matches")
    processed_at: datetime = Field(..., description="Processing time")


# Enhanced request/response models
class EnhancedPredictionRequest(BaseModel):
    """Enhanced prediction request with additional features."""

    match_id: UUID = Field(..., description="Match ID")
    model_version: Optional[str] = Field(
        None, description="Specific model version to use"
    )
    include_probabilities: bool = Field(
        True, description="Include probability breakdown"
    )
    include_expected_scores: bool = Field(
        False, description="Include expected score predictions"
    )
    include_confidence_intervals: bool = Field(
        False, description="Include confidence intervals"
    )


class PredictionHistoryResponse(BaseModel):
    """Response model for prediction history."""

    predictions: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int
    accuracy_stats: Optional[Dict[str, float]] = None


# Dependency for getting current user (placeholder)
async def get_current_user() -> User:
    """Get current authenticated user."""
    # This would be implemented with proper authentication
    # For now, return a mock user
    from ...core.security import UserRole

    return User(
        id="mock-user-id",
        username="api_user",
        email="user@example.com",
        role=UserRole.USER,
        created_at=datetime.utcnow(),
    )


@router.post(
    "/predict/single",
    response_model=LegacyPredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["predictions"],
    summary="Single match prediction",
    description="Generate prediction for a single football match",
)
@require_permission(Permission.PREDICT_READ)
async def predict_single_match(
    request: LegacySingleMatchRequest,
    model_name: Optional[str] = Query(
        None, description="Model name to use for prediction"
    ),
    current_user: User = Depends(get_current_user),
) -> LegacyPredictionResponse:
    """
    Generate prediction for a single football match.

    This endpoint provides backward compatibility with the legacy API
    while using the new prediction service architecture.
    """
    try:
        logger.info(
            "Single match prediction requested",
            home_team=request.home_team,
            away_team=request.away_team,
            match_date=request.match_date,
            user_id=current_user.id,
        )

        # Convert legacy request to new format
        # In a real implementation, you would look up match_id by teams and date
        from uuid import uuid4

        mock_match_id = uuid4()

        prediction_request = PredictionRequest(
            match_id=mock_match_id,
            model_version=model_name,
            include_probabilities=True,
            include_expected_scores=False,
        )

        # Generate prediction using the new service
        prediction_response = await prediction_service.generate_prediction(
            prediction_request
        )

        # Convert to legacy response format
        predicted_outcome_map = {
            MatchResult.HOME_WIN: "home_win",
            MatchResult.DRAW: "draw",
            MatchResult.AWAY_WIN: "away_win",
        }

        legacy_response = LegacyPredictionResponse(
            prediction_id=str(prediction_response.prediction.id),
            home_team=request.home_team,
            away_team=request.away_team,
            match_date=request.match_date,
            predicted_outcome=predicted_outcome_map[
                prediction_response.prediction.predicted_result
            ],
            confidence=prediction_response.prediction.confidence_score,
            created_at=prediction_response.prediction.created_at,
        )

        logger.info(
            "Single match prediction completed",
            prediction_id=legacy_response.prediction_id,
            predicted_outcome=legacy_response.predicted_outcome,
            confidence=legacy_response.confidence,
        )

        return legacy_response

    except ModelNotFoundError as e:
        logger.warning(
            "Model not found for prediction", model_name=model_name, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found",
        )
    except InsufficientDataError as e:
        logger.warning("Insufficient data for prediction", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Insufficient data to generate prediction",
        )
    except PredictionError as e:
        logger.error("Prediction generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction service temporarily unavailable",
        )
    except BaseApplicationError as e:
        logger.error("Application error during prediction", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.critical(
            "Unexpected error during prediction", error=str(e), exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.post(
    "/predict/batch",
    response_model=LegacyBatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["predictions"],
    summary="Batch match predictions",
    description="Generate predictions for multiple football matches",
)
@require_permission(Permission.PREDICT_READ)
async def predict_batch_matches(
    request: LegacyBatchMatchRequest,
    model_name: Optional[str] = Query(
        None, description="Model name to use for predictions"
    ),
    current_user: User = Depends(get_current_user),
) -> LegacyBatchPredictionResponse:
    """
    Generate predictions for multiple football matches.

    This endpoint processes multiple matches in parallel for improved performance.
    """
    try:
        logger.info(
            "Batch prediction requested",
            match_count=len(request.matches),
            user_id=current_user.id,
        )

        # Convert legacy requests to new format
        from uuid import uuid4

        match_ids = [uuid4() for _ in request.matches]

        batch_request = BatchPredictionRequest(
            match_ids=match_ids,
            model_version=model_name,
            include_probabilities=True,
            include_expected_scores=False,
        )

        # Generate batch predictions
        batch_response = await prediction_service.generate_batch_predictions(
            batch_request
        )

        # Convert to legacy response format
        predicted_outcome_map = {
            MatchResult.HOME_WIN: "home_win",
            MatchResult.DRAW: "draw",
            MatchResult.AWAY_WIN: "away_win",
        }

        legacy_predictions = []
        for i, pred_response in enumerate(batch_response.predictions):
            if i < len(request.matches):  # Ensure we don't exceed original request
                legacy_pred = LegacyPredictionResponse(
                    prediction_id=str(pred_response.prediction.id),
                    home_team=request.matches[i].home_team,
                    away_team=request.matches[i].away_team,
                    match_date=request.matches[i].match_date,
                    predicted_outcome=predicted_outcome_map[
                        pred_response.prediction.predicted_result
                    ],
                    confidence=pred_response.prediction.confidence_score,
                    created_at=pred_response.prediction.created_at,
                )
                legacy_predictions.append(legacy_pred)

        legacy_batch_response = LegacyBatchPredictionResponse(
            predictions=legacy_predictions,
            total_matches=len(request.matches),
            processed_at=datetime.utcnow(),
        )

        logger.info(
            "Batch prediction completed",
            total_matches=legacy_batch_response.total_matches,
            successful_predictions=len(legacy_predictions),
            failed_predictions=batch_response.failed_predictions,
        )

        return legacy_batch_response

    except Exception as e:
        logger.error("Batch prediction failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch prediction service temporarily unavailable",
        )


@router.get(
    "/history",
    response_model=PredictionHistoryResponse,
    tags=["predictions"],
    summary="Get prediction history",
    description="Retrieve historical predictions with optional filtering",
)
@require_permission(Permission.PREDICT_READ)
async def get_prediction_history(
    limit: int = Query(
        default=10, ge=1, le=100, description="Number of results to return"
    ),
    offset: int = Query(default=0, ge=0, description="Result offset for pagination"),
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    date_from: Optional[date] = Query(
        None, description="Filter predictions from this date"
    ),
    date_to: Optional[date] = Query(
        None, description="Filter predictions to this date"
    ),
    current_user: User = Depends(get_current_user),
) -> PredictionHistoryResponse:
    """
    Retrieve historical predictions with filtering and pagination.

    This endpoint provides access to past predictions for analysis and monitoring.
    """
    try:
        logger.info(
            "Prediction history requested",
            limit=limit,
            offset=offset,
            model_version=model_version,
            user_id=current_user.id,
        )

        # This would integrate with your database/analytics service
        # For now, return mock data
        mock_predictions = [
            {
                "prediction_id": "pred-001",
                "home_team": "Manchester City",
                "away_team": "Liverpool",
                "match_date": "2024-03-15",
                "predicted_outcome": "home_win",
                "actual_outcome": "draw",
                "confidence": 0.82,
                "created_at": "2024-03-14T10:30:00Z",
                "model_version": "xgb_v1.2",
            },
            {
                "prediction_id": "pred-002",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "match_date": "2024-03-14",
                "predicted_outcome": "away_win",
                "actual_outcome": "away_win",
                "confidence": 0.71,
                "created_at": "2024-03-13T15:45:00Z",
                "model_version": "xgb_v1.2",
            },
        ]

        # Apply filtering (mock implementation)
        filtered_predictions = mock_predictions
        if model_version:
            filtered_predictions = [
                p
                for p in filtered_predictions
                if p.get("model_version") == model_version
            ]

        # Apply pagination
        paginated_predictions = filtered_predictions[offset : offset + limit]

        # Calculate accuracy stats
        total_with_actual = len(
            [p for p in filtered_predictions if p.get("actual_outcome")]
        )
        correct_predictions = len(
            [
                p
                for p in filtered_predictions
                if p.get("actual_outcome")
                and p.get("predicted_outcome") == p.get("actual_outcome")
            ]
        )

        accuracy_stats = {
            "overall_accuracy": correct_predictions / total_with_actual
            if total_with_actual > 0
            else 0.0,
            "total_predictions": len(filtered_predictions),
            "predictions_with_results": total_with_actual,
        }

        response = PredictionHistoryResponse(
            predictions=paginated_predictions,
            total_count=len(filtered_predictions),
            limit=limit,
            offset=offset,
            accuracy_stats=accuracy_stats,
        )

        logger.info("Prediction history retrieved", total_count=response.total_count)
        return response

    except Exception as e:
        logger.error("Failed to retrieve prediction history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="History service temporarily unavailable",
        )
