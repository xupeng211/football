"""
Cache invalidation strategies.

Handles cache invalidation patterns and strategies for maintaining cache consistency.
"""

import asyncio
from typing import Any

import redis.asyncio as redis

from ..logging import get_logger

logger = get_logger(__name__)


class CacheInvalidator:
    """Handles cache invalidation strategies."""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.logger = get_logger(__name__)
        self._background_tasks: set[asyncio.Task[Any]] = set()

    async def invalidate_by_pattern(
        self, pattern: str, namespace: str = "default"
    ) -> int:
        """Invalidate cache entries matching a pattern."""
        try:
            redis_client = await self.cache_manager.get_redis_client()
            full_pattern = self.cache_manager._generate_key(namespace, pattern)
            keys = await redis_client.keys(full_pattern)

            if keys:
                deleted = await redis_client.delete(*keys)
                self.logger.info(
                    "Cache invalidated by pattern",
                    pattern=pattern,
                    deleted_count=deleted,
                )
                return deleted

            return 0

        except (redis.ConnectionError, redis.TimeoutError) as e:
            self.logger.error(
                "Redis connection error during invalidation",
                pattern=pattern,
                error=str(e),
            )
            return 0
        except redis.RedisError as e:
            self.logger.error(
                "Cache invalidation error",
                pattern=pattern,
                error=str(e),
            )
            return 0

    async def invalidate_by_tags(self, tags: list[str]) -> int:
        """Invalidate cache entries by tags."""
        total_deleted = 0
        for tag in tags:
            try:
                deleted = await self.invalidate_by_pattern(f"*tag:{tag}*")
                total_deleted += deleted
            except Exception as e:
                self.logger.error("Tag invalidation error", tag=tag, error=str(e))

        return total_deleted

    async def schedule_invalidation(
        self, pattern: str, delay_seconds: int, namespace: str = "default"
    ) -> None:
        """Schedule cache invalidation after a delay."""

        async def delayed_invalidation():
            await asyncio.sleep(delay_seconds)
            try:
                await self.invalidate_by_pattern(pattern, namespace)
            except Exception as e:
                self.logger.error(
                    "Scheduled invalidation error", pattern=pattern, error=str(e)
                )

        task = asyncio.create_task(delayed_invalidation())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def cleanup_background_tasks(self) -> None:
        """Clean up background invalidation tasks."""
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()
