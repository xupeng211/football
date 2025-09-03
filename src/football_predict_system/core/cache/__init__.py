"""
Caching system package.

This package provides production-grade caching capabilities with:
- Multi-level caching (memory + Redis)
- Cache invalidation strategies
- Performance monitoring
- Distributed caching support
"""

from .decorators import cached
from .invalidator import CacheInvalidator
from .manager import CacheManager
from .models import CacheStats
from .warmer import CacheWarmer

# Global cache manager instance
_cache_manager = None


async def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


__all__ = [
    "CacheInvalidator",
    "CacheManager",
    "CacheStats",
    "CacheWarmer",
    "cached",
    "get_cache_manager",
]
