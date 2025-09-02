"""
Production-grade caching system with Redis backend.

This module provides:
- Multi-level caching (memory + Redis)
- Cache invalidation strategies
- Performance monitoring
- Distributed caching support
"""

import asyncio
import json
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import redis.asyncio as redis
from pydantic import BaseModel

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)


class CacheStats(BaseModel):
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheManager:
    """Manages multi-level caching with Redis backend."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self._redis_client: redis.Redis | None = None  # type: ignore
        self._memory_cache: dict[str, dict[str, Any]] = {}
        self._stats = CacheStats()
        self._max_memory_items = 1000
        self._default_ttl = 3600  # 1 hour

    async def get_redis_client(self) -> redis.Redis:  # type: ignore
        """Get or create Redis client."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                self.settings.redis.url,
                max_connections=self.settings.redis.max_connections,
                retry_on_timeout=self.settings.redis.retry_on_timeout,
                socket_timeout=self.settings.redis.socket_timeout,
                decode_responses=False,  # We handle encoding ourselves
            )
        return self._redis_client

    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace."""
        return f"{self.settings.app_name}:{namespace}:{key}"

    def _is_expired(self, cache_entry: dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if "expires_at" not in cache_entry:
            return False
        return bool(datetime.now() > cache_entry["expires_at"])

    async def get(self, key: str, namespace: str = "default") -> Any | None:
        """Get value from cache (memory first, then Redis)."""
        cache_key = self._generate_key(namespace, key)

        try:
            # Try memory cache first
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if not self._is_expired(entry):
                    self._stats.hits += 1
                    self.logger.debug("Cache hit (memory)", key=cache_key)
                    return entry["value"]
                else:
                    # Remove expired entry
                    del self._memory_cache[cache_key]

            # Try Redis cache
            redis_client = await self.get_redis_client()
            cached_data = await redis_client.get(cache_key)

            if cached_data is not None:
                try:
                    # Use JSON for safer deserialization
                    value = json.loads(cached_data.decode("utf-8"))

                    # Store in memory cache for faster access
                    if len(self._memory_cache) < self._max_memory_items:
                        self._memory_cache[cache_key] = {
                            "value": value,
                            "expires_at": datetime.now()
                            + timedelta(seconds=300),  # 5 min in memory
                        }

                    self._stats.hits += 1
                    self.logger.debug("Cache hit (Redis)", key=cache_key)
                    return value

                except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as e:
                    self.logger.warning(
                        "Failed to deserialize cached data",
                        key=cache_key,
                        error=str(e),
                    )
                    await redis_client.delete(cache_key)

            self._stats.misses += 1
            self.logger.debug("Cache miss", key=cache_key)
            return None

        except Exception as e:
            self._stats.errors += 1
            self.logger.error("Cache get error", key=cache_key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        namespace: str = "default",
    ) -> bool:
        """Set value in cache."""
        cache_key = self._generate_key(namespace, key)
        ttl = ttl or self._default_ttl

        try:
            # Store in Redis using JSON serialization
            redis_client = await self.get_redis_client()
            try:
                serialized_value = json.dumps(value, default=str).encode("utf-8")
            except (TypeError, ValueError) as e:
                self.logger.warning("Failed to serialize value with JSON", error=str(e))
                return False
            await redis_client.setex(cache_key, ttl, serialized_value)

            # Store in memory cache
            if len(self._memory_cache) < self._max_memory_items:
                self._memory_cache[cache_key] = {
                    "value": value,
                    "expires_at": datetime.now() + timedelta(seconds=min(ttl, 300)),
                }

            self._stats.sets += 1
            self.logger.debug("Cache set", key=cache_key, ttl=ttl)
            return True

        except Exception as e:
            self._stats.errors += 1
            self.logger.error("Cache set error", key=cache_key, error=str(e))
            return False

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete value from cache."""
        cache_key = self._generate_key(namespace, key)

        try:
            # Remove from memory cache
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]

            # Remove from Redis
            redis_client = await self.get_redis_client()
            result = await redis_client.delete(cache_key)

            self._stats.deletes += 1
            self.logger.debug("Cache delete", key=cache_key, found=result > 0)
            return result > 0

        except Exception as e:
            self._stats.errors += 1
            self.logger.error("Cache delete error", key=cache_key, error=str(e))
            return False

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        pattern = self._generate_key(namespace, "*")

        try:
            redis_client = await self.get_redis_client()
            keys = await redis_client.keys(pattern)

            if keys:
                deleted = await redis_client.delete(*keys)
            else:
                deleted = 0

            # Clear from memory cache
            memory_keys_to_delete = [
                k
                for k in self._memory_cache.keys()
                if k.startswith(f"{self.settings.app_name}:{namespace}:")
            ]
            for key in memory_keys_to_delete:
                del self._memory_cache[key]

            self.logger.info(
                "Cache namespace cleared",
                namespace=namespace,
                deleted_count=deleted,
            )
            return deleted

        except Exception as e:
            self.logger.error(
                "Cache clear namespace error",
                namespace=namespace,
                error=str(e),
            )
            return 0

    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if key exists in cache."""
        cache_key = self._generate_key(namespace, key)

        try:
            # Check memory cache first
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                if not self._is_expired(entry):
                    return True
                else:
                    del self._memory_cache[cache_key]

            # Check Redis
            redis_client = await self.get_redis_client()
            return await redis_client.exists(cache_key) > 0

        except Exception as e:
            self.logger.error("Cache exists error", key=cache_key, error=str(e))
            return False

    async def get_ttl(self, key: str, namespace: str = "default") -> int:
        """Get TTL for a key."""
        cache_key = self._generate_key(namespace, key)

        try:
            redis_client = await self.get_redis_client()
            return await redis_client.ttl(cache_key)
        except Exception as e:
            self.logger.error("Cache TTL error", key=cache_key, error=str(e))
            return -1

    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        return self._stats

    def clear_memory_cache(self) -> None:
        """Clear memory cache."""
        self._memory_cache.clear()
        self.logger.info("Memory cache cleared")

    async def health_check(self) -> dict[str, Any]:
        """Perform cache health check."""
        try:
            redis_client = await self.get_redis_client()

            # Test Redis connectivity
            start_time = time.time()
            await redis_client.ping()
            redis_response_time = time.time() - start_time

            # Get Redis info
            info = await redis_client.info()

            return {
                "status": "healthy",
                "redis_connected": True,
                "redis_response_time": redis_response_time,
                "memory_cache_size": len(self._memory_cache),
                "stats": self._stats.dict(),
                "redis_info": {
                    "version": info.get("redis_version"),
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                },
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "memory_cache_size": len(self._memory_cache),
                "stats": self._stats.dict(),
            }

    async def close(self) -> None:
        """Close cache connections."""
        if self._redis_client:
            await self._redis_client.close()
            self.logger.info("Redis client closed")


# Global cache manager instance
_cache_manager: CacheManager | None = None


async def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(
    ttl: int = 3600,
    namespace: str = "default",
    key_func: Callable[..., Any] | None = None,
) -> Callable[..., Any]:
    """Decorator for caching function results."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_manager = await get_cache_manager()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl, namespace)

            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For synchronous functions, we need to run in event loop
            async def _async_cached() -> Any:
                return await async_wrapper(*args, **kwargs)

            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(_async_cached())
            except RuntimeError:
                # No event loop running, create one
                return asyncio.run(_async_cached())

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class CacheInvalidator:
    """Handles cache invalidation strategies."""

    def __init__(self, cache_manager: CacheManager):
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

        except Exception as e:
            self.logger.error(
                "Cache invalidation error",
                pattern=pattern,
                error=str(e),
            )
            return 0

    async def invalidate_by_tags(
        self, tags: list[str], namespace: str = "default"
    ) -> int:
        """Invalidate cache entries by tags."""
        total_deleted = 0

        for tag in tags:
            pattern = f"*:{tag}:*"
            deleted = await self.invalidate_by_pattern(pattern, namespace)
            total_deleted += deleted

        return total_deleted

    async def schedule_invalidation(
        self, key: str, delay: int, namespace: str = "default"
    ) -> None:
        """Schedule cache invalidation after delay."""

        async def _delayed_invalidation() -> None:
            await asyncio.sleep(delay)
            await self.cache_manager.delete(key, namespace)
            self.logger.info(
                "Scheduled cache invalidation executed", key=key, delay=delay
            )

        task = asyncio.create_task(_delayed_invalidation())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)


# Cache warming utilities
class CacheWarmer:
    """Handles cache warming strategies."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = get_logger(__name__)

    async def warm_predictions(self, match_ids: list[str]) -> None:
        """Pre-warm prediction cache for upcoming matches."""
        self.logger.info(
            "Starting prediction cache warming", match_count=len(match_ids)
        )

        # This would integrate with your prediction service
        # For now, it's a placeholder for the concept
        for match_id in match_ids:
            try:
                # Simulate prediction generation and caching
                cache_key = f"prediction:{match_id}"

                # Check if already cached
                if not await self.cache_manager.exists(cache_key, "predictions"):
                    # Generate prediction (placeholder)
                    prediction_data = {
                        "match_id": match_id,
                        "prediction": "placeholder",
                    }
                    await self.cache_manager.set(
                        cache_key, prediction_data, 7200, "predictions"
                    )  # 2 hours

            except Exception as e:
                self.logger.error(
                    "Cache warming failed for match",
                    match_id=match_id,
                    error=str(e),
                )

        self.logger.info("Prediction cache warming completed")

    async def warm_model_metadata(self) -> None:
        """Pre-warm model metadata cache."""
        self.logger.info("Starting model metadata cache warming")

        try:
            # This would integrate with your model registry
            # Placeholder implementation
            models_data: dict[str, Any] = {
                "available_models": [],
                "default_model": None,
            }
            await self.cache_manager.set("models_metadata", models_data, 3600, "models")

        except Exception as e:
            self.logger.error("Model metadata cache warming failed", error=str(e))

        self.logger.info("Model metadata cache warming completed")
