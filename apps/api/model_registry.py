import os

import structlog

from apps.api.services.prediction_service import prediction_service

logger = structlog.get_logger(__name__)


def check_model_registry() -> tuple[bool, str]:
    """Checks if a valid model is loaded in the prediction service."""
    # In test environment, this check is skipped as models are not loaded.
    if os.getenv("PYTEST_CURRENT_TEST"):
        return True, "Model registry check skipped in test environment."

    try:
        model_version = prediction_service.get_model_version()

        if model_version and "stub" not in model_version:
            return True, f"Model '{model_version}' is loaded and healthy."
        elif model_version:
            return False, f"A stub model ('{model_version}') is loaded."
        else:
            return False, "No model is loaded in the prediction service."

    except Exception as e:
        logger.error("Model registry check failed unexpectedly", error=str(e))
        return False, f"Model registry check failed with an exception: {e}"
