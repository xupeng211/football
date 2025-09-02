"""
Main router for API v1.

This module aggregates all API v1 endpoint routers.
"""

from fastapi import APIRouter

# Import endpoint routers
from .models import router as models_router
from .predictions import router as predictions_router

# from .data import router as data_router
# from .monitoring import router as monitoring_router


router = APIRouter()

# Include endpoint routers
router.include_router(predictions_router, prefix="/predict", tags=["predictions"])
router.include_router(models_router, prefix="/models", tags=["models"])
# router.include_router(data_router, prefix="/data", tags=["data"])
# router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])


@router.get("/status", tags=["general"])
async def get_api_status() -> dict[str, str]:
    """Get API v1 status."""
    return {"status": "ok", "version": "v1"}
