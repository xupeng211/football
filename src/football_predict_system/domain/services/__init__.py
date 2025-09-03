"""
Domain services package.

Contains business logic services that orchestrate domain operations.
"""

from .analytics_service import AnalyticsService
from .data_service import DataService
from .model_service import ModelService, get_model_service
from .prediction_service import PredictionService

# Global service instances
_prediction_service: PredictionService | None = None


def get_prediction_service() -> PredictionService:
    """Get global prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service


# Create global instance for backward compatibility
prediction_service = get_prediction_service()

__all__ = [
    "AnalyticsService",
    "DataService",
    "ModelService",
    "PredictionService",
    "get_model_service",
    "get_prediction_service",
    "prediction_service",
]
