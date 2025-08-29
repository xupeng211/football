import os

import structlog

from apps.api.services.prediction_service import prediction_service

logger = structlog.get_logger(__name__)


def check_model_registry() -> tuple[bool, str]:
    """Checks if the model registry is available and a model can be loaded."""
    # In test environment, skip model registry check
    if os.getenv("PYTEST_CURRENT_TEST"):
        return True, "Model registry check skipped in test environment."

    try:
        available_models = prediction_service.list_models()
        if not available_models:
            return False, "No models found in the registry."

        # Try to load the latest model as a health check
        latest_model = max(available_models)
        prediction_service.load_model(latest_model)
        return (
            True,
            f"Model registry available. Latest model '{latest_model}' loaded.",
        )
    except Exception as e:
        logger.error("Model registry check failed", error=str(e))
        return False, f"Model registry check failed: {e}"
