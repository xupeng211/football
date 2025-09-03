"""
Cache manager implementation.

Handles multi-level caching with Redis backend and memory cache.
"""

import asyncio
import json
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

import redis.asyncio as redis

from ..config import get_settings
from ..logging import get_logger
from .models import CacheStats

logger = get_logger(__name__)


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

        except (redis.ConnectionError, redis.TimeoutError) as e:
            self._stats.errors += 1
            self.logger.error("Redis connection error", key=cache_key, error=str(e))
            return None
        except redis.RedisError as e:
            self._stats.errors += 1
            self.logger.error("Redis operation error", key=cache_key, error=str(e))
            return None
        except (json.JSONDecodeError, ValueError) as e:
            self._stats.errors += 1
            self.logger.error("Cache data decode error", key=cache_key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        namespace: str = "default",
    ) -> bool:
        """Set value in cache (both memory and Redis)."""
        cache_key = self._generate_key(namespace, key)
        ttl = ttl or self._default_ttl

        try:
            # Serialize the value
            serialized_value = json.dumps(value, default=str)

            # Store in Redis
            redis_client = await self.get_redis_client()
            await redis_client.setex(cache_key, ttl, serialized_value)

            # Store in memory cache (with shorter TTL)
            if len(self._memory_cache) < self._max_memory_items:
                memory_ttl = min(ttl, 300)  # Max 5 minutes in memory
                self._memory_cache[cache_key] = {
                    "value": value,
                    "expires_at": datetime.now() + timedelta(seconds=memory_ttl),
                }

            self._stats.sets += 1
            self.logger.debug("Cache set", key=cache_key, ttl=ttl)
            return True

        except (redis.ConnectionError, redis.TimeoutError) as e:
            self._stats.errors += 1
            self.logger.error("Redis connection error", key=cache_key, error=str(e))
            return False
        except redis.RedisError as e:
            self._stats.errors += 1
            self.logger.error("Redis operation error", key=cache_key, error=str(e))
            return False
        except (TypeError, ValueError) as e:
            self._stats.errors += 1
            self.logger.error("Cache data encode error", key=cache_key, error=str(e))
            return False

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete value from cache."""
        cache_key = self._generate_key(namespace, key)

        try:
            # Remove from memory cache
            self._memory_cache.pop(cache_key, None)

            # Remove from Redis
            redis_client = await self.get_redis_client()
            result = await redis_client.delete(cache_key)

            self._stats.deletes += 1
            self.logger.debug("Cache delete", key=cache_key, existed=bool(result))
            return bool(result)

        except (redis.ConnectionError, redis.TimeoutError) as e:
            self._stats.errors += 1
            self.logger.error("Redis connection error", key=cache_key, error=str(e))
            return False
        except redis.RedisError as e:
            self._stats.errors += 1
            self.logger.error("Redis operation error", key=cache_key, error=str(e))
            return False

    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if key exists in cache."""
        cache_key = self._generate_key(namespace, key)

        # Check memory cache first
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not self._is_expired(entry):
                return True
            else:
                del self._memory_cache[cache_key]

        # Check Redis
        try:
            redis_client = await self.get_redis_client()
            result = await redis_client.exists(cache_key)
            return bool(result)
        except redis.RedisError as e:
            self.logger.error("Cache exists check error", key=cache_key, error=str(e))
            return False

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        try:
            pattern = f"{self.settings.app_name}:{namespace}:*"
            redis_client = await self.get_redis_client()
            keys = await redis_client.keys(pattern)

            if keys:
                deleted = await redis_client.delete(*keys)
                # Also clear from memory cache
                for cache_key in list(self._memory_cache.keys()):
                    if cache_key.startswith(f"{self.settings.app_name}:{namespace}:"):
                        del self._memory_cache[cache_key]

                self.logger.info(
                    "Namespace cleared", namespace=namespace, deleted_count=deleted
                )
                return deleted

            return 0

        except redis.RedisError as e:
            self.logger.error(
                "Namespace clear error", namespace=namespace, error=str(e)
            )
            return 0

    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        return self._stats

    def cache(
        self,
        key_func: Callable[..., str] | None = None,
        ttl: int | None = None,
        namespace: str = "default",
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator for caching function results."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation
                    key_parts = [func.__name__]
                    key_parts.extend(str(arg) for arg in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = "|".join(key_parts)

                # Try to get from cache
                cached_result = await self.get(cache_key, namespace)
                if cached_result is not None:
                    return cached_result

                # Call function and cache result
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                await self.set(cache_key, result, ttl, namespace)
                return result

            return wrapper

        return decorator

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
