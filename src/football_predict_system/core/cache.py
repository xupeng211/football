"""
Production-grade caching system with Redis backend.

This module provides:
- Multi-level caching (memory + Redis)
- Cache invalidation strategies
- Performance monitoring
- Distributed caching support
"""

# Re-export for backward compatibility
from .cache import get_cache_manager
from .cache.manager import CacheManager
from .cache.models import CacheStats

__all__ = ["CacheManager", "CacheStats", "get_cache_manager"]
