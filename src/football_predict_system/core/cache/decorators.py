"""
Cache decorators for easy function caching.

Provides decorators for caching function results with various strategies.
"""

import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

from .manager import CacheManager


def cached(
    ttl: int = 300, key_prefix: str = "", namespace: str = "default"
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        namespace: Cache namespace

    Returns:
        Decorated function with caching capability
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache manager instance
            cache_manager = CacheManager()

            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__] if key_prefix else [func.__name__]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

            cache_key = ":".join(key_parts)

            # Try to get from cache
            try:
                cached_result = await cache_manager.get(cache_key, namespace)
                if cached_result is not None:
                    return cached_result
            except Exception:
                pass  # Cache miss or error, continue to function execution  # nosec B110

            # Execute function and cache result
            result = await func(*args, **kwargs)

            try:
                await cache_manager.set(cache_key, result, ttl, namespace)
            except Exception:
                pass  # Cache error, but return result anyway  # nosec B110

            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For synchronous functions, just return the result without caching
            # In a real implementation, you might want to use a synchronous cache
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
