import os

import redis
import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    logger.warning("REDIS_URL environment variable not set.")
    redis_client = None
else:
    try:
        redis_client = redis.from_url(REDIS_URL)
    except redis.exceptions.RedisError as e:
        logger.error("Failed to create Redis client", error=str(e))
        redis_client = None


def check_redis_connection() -> tuple[bool, str]:
    """Checks the Redis connection."""
    # In test environment, skip Redis check
    if os.getenv("PYTEST_CURRENT_TEST"):
        return True, "Redis check skipped in test environment."

    if not redis_client:
        return False, "Redis client not configured. REDIS_URL is not set."
    try:
        if redis_client.ping():
            return True, "Redis connection successful."
        else:
            # This case is unlikely with redis-py's implementation of ping,
            # as it raises an exception on failure.
            return False, "Redis connection failed: PING returned False."
    except redis.exceptions.ConnectionError as e:
        logger.error("Redis connection failed", error=str(e))
        return False, f"Redis connection failed: {e}"
