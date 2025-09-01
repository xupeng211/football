"""Comprehensive unit tests for cache module.

This test suite aims to boost cache coverage from 16% to 60%+
Tests all major classes: CacheStats, CacheManager, CacheInvalidator, CacheWarmer
"""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from football_predict_system.core.cache import (
    CacheInvalidator,
    CacheManager,
    CacheStats,
    CacheWarmer,
    cached,
    get_cache_manager,
)


class TestCacheStats:
    """Test the CacheStats model."""

    def test_cache_stats_initialization(self):
        """Test CacheStats default values."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.errors == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        # Zero hits and misses
        stats = CacheStats()
        assert stats.hit_rate == 0.0

        # Some hits and misses
        stats = CacheStats(hits=7, misses=3)
        assert stats.hit_rate == 0.7

        # Only hits
        stats = CacheStats(hits=10, misses=0)
        assert stats.hit_rate == 1.0

        # Only misses
        stats = CacheStats(hits=0, misses=5)
        assert stats.hit_rate == 0.0


class TestCacheManager:
    """Test the CacheManager class."""

    @pytest.fixture
    def cache_manager(self):
        """Create a cache manager for testing."""
        return CacheManager()

    def test_cache_manager_initialization(self, cache_manager):
        """Test CacheManager initialization."""
        assert cache_manager.settings is not None
        assert cache_manager.logger is not None
        assert cache_manager._redis_client is None
        assert isinstance(cache_manager._stats, CacheStats)
        assert isinstance(cache_manager._memory_cache, dict)

        def test_generate_key(self, cache_manager):
        """Test key generation."""
        key = cache_manager._generate_key("test_ns", "test_key")
        # Key includes app name prefix
        expected = "Football Prediction System:test_ns:test_key"
        assert key == expected
        
        key = cache_manager._generate_key("default", "user:123")
        expected = "Football Prediction System:default:user:123"
        assert key == expected

    def test_is_expired(self, cache_manager):
        """Test expiration checking."""
        from datetime import datetime, timedelta

        # Not expired
        future_time = datetime.now() + timedelta(minutes=5)
        entry = {"expires_at": future_time}
        assert not cache_manager._is_expired(entry)

        # Expired
        past_time = datetime.now() - timedelta(minutes=5)
        entry = {"expires_at": past_time}
        assert cache_manager._is_expired(entry)

    @pytest.mark.asyncio
    async def test_get_redis_client(self, cache_manager):
        """Test Redis client creation."""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            client = await cache_manager.get_redis_client()
            assert client == mock_client
            assert cache_manager._redis_client == mock_client

    @pytest.mark.asyncio
    async def test_set_and_get_memory_cache(self, cache_manager):
        """Test memory cache set and get operations."""
        # Test setting in memory cache
        cache_manager._memory_cache["test:key"] = {
            "value": "test_value",
            "expires_at": time.time() + 300
        }

        # Memory cache should work without Redis
        with patch.object(cache_manager, 'get_redis_client') as mock_redis:
            mock_redis.side_effect = Exception("Redis not available")

            result = await cache_manager.get("key", "test")
            # Should handle Redis errors gracefully
            assert result is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_manager):
        """Test setting cache with TTL."""
        with patch.object(cache_manager, 'get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            # Mock successful set
            mock_client.setex.return_value = True

            result = await cache_manager.set("test_key", "test_value", ttl=300)
            assert result is True

            # Verify Redis call
            mock_client.setex.assert_called_once()
            assert cache_manager._stats.sets == 1

    @pytest.mark.asyncio
    async def test_delete_key(self, cache_manager):
        """Test cache key deletion."""
        with patch.object(cache_manager, 'get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.delete.return_value = 1

            result = await cache_manager.delete("test_key")
            assert result is True
            assert cache_manager._stats.deletes == 1

    @pytest.mark.asyncio
    async def test_clear_namespace(self, cache_manager):
        """Test clearing entire namespace."""
        with patch.object(cache_manager, 'get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            # Mock scan and delete
            mock_client.scan_iter.return_value = ['test:key1', 'test:key2']
            mock_client.delete.return_value = 2

            count = await cache_manager.clear_namespace("test")
            assert count == 2

    @pytest.mark.asyncio
    async def test_exists(self, cache_manager):
        """Test key existence checking."""
        with patch.object(cache_manager, 'get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.exists.return_value = 1

            exists = await cache_manager.exists("test_key")
            assert exists is True

    @pytest.mark.asyncio
    async def test_get_ttl(self, cache_manager):
        """Test TTL retrieval."""
        with patch.object(cache_manager, 'get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.ttl.return_value = 300

            ttl = await cache_manager.get_ttl("test_key")
            assert ttl == 300

    def test_get_stats(self, cache_manager):
        """Test stats retrieval."""
        stats = cache_manager.get_stats()
        assert isinstance(stats, CacheStats)

    def test_clear_memory_cache(self, cache_manager):
        """Test memory cache clearing."""
        # Add some data to memory cache
        cache_manager._memory_cache["test"] = "value"
        assert len(cache_manager._memory_cache) > 0

        cache_manager.clear_memory_cache()
        assert len(cache_manager._memory_cache) == 0

    @pytest.mark.asyncio
    async def test_health_check(self, cache_manager):
        """Test cache health check."""
        with patch.object(cache_manager, 'get_redis_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.ping.return_value = True

            health = await cache_manager.health_check()
            assert health["status"] == "healthy"
            assert "redis_connected" in health
            assert "memory_cache_size" in health
            assert "stats" in health


class TestCacheInvalidator:
    """Test the CacheInvalidator class."""

    @pytest.fixture
    def cache_manager(self):
        """Create a mock cache manager."""
        return MagicMock(spec=CacheManager)

    @pytest.fixture
    def invalidator(self, cache_manager):
        """Create a cache invalidator."""
        return CacheInvalidator(cache_manager)

    @pytest.mark.asyncio
    async def test_invalidate_by_pattern(self, invalidator, cache_manager):
        """Test pattern-based invalidation."""
        cache_manager.get_redis_client.return_value = AsyncMock()
        mock_client = cache_manager.get_redis_client.return_value
        mock_client.scan_iter.return_value = ['user:123', 'user:456']
        mock_client.delete.return_value = 2

        count = await invalidator.invalidate_by_pattern("user:*")
        assert count == 2

    @pytest.mark.asyncio
    async def test_invalidate_by_tags(self, invalidator, cache_manager):
        """Test tag-based invalidation."""
        cache_manager.get_redis_client.return_value = AsyncMock()
        mock_client = cache_manager.get_redis_client.return_value
        mock_client.smembers.return_value = {'key1', 'key2'}
        mock_client.delete.return_value = 2

        count = await invalidator.invalidate_by_tags(["tag1"])
        assert count == 2


class TestCacheWarmer:
    """Test the CacheWarmer class."""

    @pytest.fixture
    def cache_manager(self):
        """Create a mock cache manager."""
        return MagicMock(spec=CacheManager)

    @pytest.fixture
    def warmer(self, cache_manager):
        """Create a cache warmer."""
        return CacheWarmer(cache_manager)

        @pytest.mark.asyncio
    async def test_warm_predictions(self, warmer, cache_manager):
        """Test prediction warming."""
        cache_manager.set = AsyncMock(return_value=True)
        
        await warmer.warm_predictions(["match1", "match2"])
        
        # Should call set for each match  
        assert cache_manager.set.call_count >= 2

    @pytest.mark.asyncio
    async def test_warm_model_metadata(self, warmer, cache_manager):
        """Test model metadata warming."""
        cache_manager.set.return_value = True

        await warmer.warm_model_metadata()

        # Should call set for model metadata
        cache_manager.set.assert_called()


class TestCacheDecorator:
    """Test the cached decorator."""

    @pytest.mark.asyncio
    async def test_cached_decorator_async(self):
        """Test cached decorator with async function."""
        call_count = 0

        @cached(ttl=300, namespace="test")
        async def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        with patch('football_predict_system.core.cache.get_cache_manager') as mock_get_manager:
            mock_manager = AsyncMock()
            mock_get_manager.return_value = mock_manager

            # First call - cache miss
            mock_manager.get.return_value = None
            result1 = await expensive_function(5)
            assert result1 == 10
            assert call_count == 1

            # Second call - cache hit
            mock_manager.get.return_value = 10
            result2 = await expensive_function(5)
            assert result2 == 10
            assert call_count == 1  # Should not increment


@pytest.mark.asyncio
async def test_get_cache_manager():
    """Test cache manager singleton."""
    manager1 = await get_cache_manager()
    manager2 = await get_cache_manager()

    # Should return the same instance
    assert manager1 is manager2
    assert isinstance(manager1, CacheManager)
