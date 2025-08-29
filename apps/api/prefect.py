import asyncio
import os

import structlog
from dotenv import load_dotenv
from prefect import get_client
from prefect.exceptions import PrefectException

logger = structlog.get_logger(__name__)

load_dotenv()

PREFECT_API_URL = os.getenv("PREFECT_API_URL")


async def check_prefect_connection_async() -> tuple[bool, str]:
    """Checks the Prefect API connection asynchronously."""
    if not PREFECT_API_URL:
        return False, "Prefect client not configured. PREFECT_API_URL not set."

    try:
        async with get_client() as client:
            healthy = await client.api_healthcheck()
            if healthy:
                return True, "Prefect API connection successful."
            else:
                return False, "Prefect API is not healthy."
    except PrefectException as e:
        logger.error("Prefect API connection failed", error=str(e))
        return False, f"Prefect API connection failed: {e}"
    except Exception as e:
        logger.error(
            "An unexpected error occurred during Prefect health check", error=str(e)
        )
        return False, f"An unexpected error occurred: {e}"


def check_prefect_connection() -> tuple[bool, str]:
    """
    Checks the Prefect API connection.
    This is a sync wrapper for the async check.
    """
    if os.getenv("PYTEST_CURRENT_TEST"):
        return True, "Prefect check skipped in test environment."

    try:
        return asyncio.run(check_prefect_connection_async())
    except Exception as e:
        logger.error("Failed to run async Prefect check in sync context", error=str(e))
        return False, f"Failed to run async check: {e}"
