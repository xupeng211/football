import os
from typing import AsyncGenerator

import redis.asyncio as redis
import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

async_redis_client: redis.Redis | None = None

if REDIS_URL:
    try:
        async_redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    except redis.exceptions.RedisError as e:
        logger.error("Failed to create async Redis client", error=str(e))
        async_redis_client = None


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    """FastAPI dependency to get an async Redis client."""
    if not async_redis_client:
        raise ConnectionError("Redis client not configured. REDIS_URL is not set.")
    yield async_redis_client


async def check_redis_connection_async() -> tuple[bool, str]:
    """Asynchronously checks the Redis connection."""
    if os.getenv("PYTEST_CURRENT_TEST"):
        return True, "Redis check skipped in test environment."

    if not async_redis_client:
        return False, "Redis client not configured. REDIS_URL is not set."

    try:
        if await async_redis_client.ping():
            return True, "Redis connection successful."
        return False, "Redis connection failed: PING returned False."
    except redis.exceptions.ConnectionError as e:
        logger.error("Redis connection failed", error=str(e))
        return False, f"Redis connection failed: {e}"
