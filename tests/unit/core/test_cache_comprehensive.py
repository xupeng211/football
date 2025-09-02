"""
Comprehensive tests for the cache module to improve coverage to 80%.

Tests all major functionality including:
- CacheStats
- CacheManager operations
- Memory and Redis caching
- Error handling
- Decorators
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from football_predict_system.core.cache import (
    CacheManager,
    CacheStats,
    get_cache_manager,
)


class TestCacheStats:
    """Test cache statistics functionality."""

    def test_cache_stats_initialization(self):
        """Test CacheStats model initialization."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.errors == 0

    def test_cache_stats_with_values(self):
        """Test CacheStats with initial values."""
        stats = CacheStats(hits=10, misses=5, sets=8, deletes=2, errors=1)
        assert stats.hits == 10
        assert stats.misses == 5
        assert stats.sets == 8
        assert stats.deletes == 2
        assert stats.errors == 1

    def test_hit_rate_calculation_zero_operations(self):
        """Test hit rate calculation with zero operations."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation_with_hits_and_misses(self):
        """Test hit rate calculation with hits and misses."""
        stats = CacheStats(hits=80, misses=20)
        assert stats.hit_rate == 0.8

    def test_hit_rate_calculation_only_hits(self):
        """Test hit rate calculation with only hits."""
        stats = CacheStats(hits=100, misses=0)
        assert stats.hit_rate == 1.0

    def test_hit_rate_calculation_only_misses(self):
        """Test hit rate calculation with only misses."""
        stats = CacheStats(hits=0, misses=50)
        assert stats.hit_rate == 0.0


class TestCacheManager:
    """Test CacheManager functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.cache_manager = CacheManager()

    def test_cache_manager_initialization(self):
        """Test CacheManager initialization."""
        manager = CacheManager()
        assert manager._redis_client is None
        assert manager._memory_cache == {}
        assert isinstance(manager._stats, CacheStats)
        assert manager._max_memory_items == 1000
        assert manager._default_ttl == 3600

    def test_generate_key(self):
        """Test cache key generation."""
        key = self.cache_manager._generate_key("test_namespace", "test_key")
        expected = f"{self.cache_manager.settings.app_name}:test_namespace:test_key"
        assert key == expected

    def test_generate_key_default_namespace(self):
        """Test cache key generation with default namespace."""
        key = self.cache_manager._generate_key("default", "my_key")
        expected = f"{self.cache_manager.settings.app_name}:default:my_key"
        assert key == expected

    def test_is_expired_no_expiry(self):
        """Test expiry check for entry without expiry."""
        entry = {"value": "test"}
        assert not self.cache_manager._is_expired(entry)

    def test_is_expired_not_expired(self):
        """Test expiry check for non-expired entry."""
        future_time = datetime.now() + timedelta(minutes=10)
        entry = {"value": "test", "expires_at": future_time}
        assert not self.cache_manager._is_expired(entry)

    def test_is_expired_expired(self):
        """Test expiry check for expired entry."""
        past_time = datetime.now() - timedelta(minutes=10)
        entry = {"value": "test", "expires_at": past_time}
        assert self.cache_manager._is_expired(entry)

    @pytest.mark.asyncio
    async def test_get_redis_client(self):
        """Test Redis client creation."""
        with patch("redis.asyncio.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            client = await self.cache_manager.get_redis_client()
            assert client == mock_client
            assert self.cache_manager._redis_client == mock_client

            # Second call should return cached client
            client2 = await self.cache_manager.get_redis_client()
            assert client2 == mock_client
            mock_redis.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_memory_cache_hit(self):
        """Test cache get with memory cache hit."""
        cache_key = "test_app:default:test_key"
        test_value = {"data": "test"}
        future_time = datetime.now() + timedelta(minutes=10)

        self.cache_manager._memory_cache[cache_key] = {
            "value": test_value,
            "expires_at": future_time,
        }

        result = await self.cache_manager.get("test_key")
        assert result == test_value
        assert self.cache_manager._stats.hits == 1
        assert self.cache_manager._stats.misses == 0

    @pytest.mark.asyncio
    async def test_get_memory_cache_expired(self):
        """Test cache get with expired memory cache entry."""
        cache_key = "test_app:default:test_key"
        test_value = {"data": "test"}
        past_time = datetime.now() - timedelta(minutes=10)

        self.cache_manager._memory_cache[cache_key] = {
            "value": test_value,
            "expires_at": past_time,
        }

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = None
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.get("test_key")
            assert result is None
            assert cache_key not in self.cache_manager._memory_cache
            assert self.cache_manager._stats.misses == 1

    @pytest.mark.asyncio
    async def test_get_redis_cache_hit(self):
        """Test cache get with Redis cache hit."""
        test_value = {"data": "test"}
        serialized_value = json.dumps(test_value).encode("utf-8")

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = serialized_value
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.get("test_key")
            assert result == test_value
            assert self.cache_manager._stats.hits == 1

    @pytest.mark.asyncio
    async def test_get_redis_cache_invalid_json(self):
        """Test cache get with invalid JSON from Redis."""
        invalid_data = b"invalid json"

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = invalid_data
            mock_client.delete = AsyncMock()
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.get("test_key")
            assert result is None
            mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_miss(self):
        """Test cache get with complete miss."""
        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.get.return_value = None
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.get("test_key")
            assert result is None
            assert self.cache_manager._stats.misses == 1

    @pytest.mark.asyncio
    async def test_get_exception_handling(self):
        """Test cache get with exception."""
        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_redis_client.side_effect = Exception("Redis connection failed")

            result = await self.cache_manager.get("test_key")
            assert result is None
            assert self.cache_manager._stats.errors == 1

    @pytest.mark.asyncio
    async def test_set_success(self):
        """Test successful cache set operation."""
        test_value = {"data": "test"}

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.setex = AsyncMock()
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.set("test_key", test_value)
            assert result is True
            assert self.cache_manager._stats.sets == 1
            mock_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_custom_ttl(self):
        """Test cache set with custom TTL."""
        test_value = {"data": "test"}
        custom_ttl = 1800

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.setex = AsyncMock()
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.set(
                "test_key", test_value, ttl=custom_ttl
            )
            assert result is True

            # Check that setex was called with custom TTL
            args, kwargs = mock_client.setex.call_args
            assert args[1] == custom_ttl  # TTL argument

    @pytest.mark.asyncio
    async def test_set_serialization_error(self):
        """Test cache set with serialization error."""

        # Create an object that can't be JSON serialized
        class UnserializableObject:
            def __init__(self):
                self.circular_ref = self

        unserializable_value = UnserializableObject()

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.set("test_key", unserializable_value)
            assert result is False

    @pytest.mark.asyncio
    async def test_set_exception_handling(self):
        """Test cache set with exception."""
        test_value = {"data": "test"}

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_redis_client.side_effect = Exception("Redis connection failed")

            result = await self.cache_manager.set("test_key", test_value)
            assert result is False
            assert self.cache_manager._stats.errors == 1

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Test successful cache delete operation."""
        cache_key = "test_app:default:test_key"
        self.cache_manager._memory_cache[cache_key] = {"value": "test"}

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.delete.return_value = 1  # Key found and deleted
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.delete("test_key")
            assert result is True
            assert cache_key not in self.cache_manager._memory_cache
            assert self.cache_manager._stats.deletes == 1

    @pytest.mark.asyncio
    async def test_delete_key_not_found(self):
        """Test cache delete when key not found."""
        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.delete.return_value = 0  # Key not found
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.delete("nonexistent_key")
            assert result is False
            assert self.cache_manager._stats.deletes == 1

    @pytest.mark.asyncio
    async def test_delete_exception_handling(self):
        """Test cache delete with exception."""
        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_redis_client.side_effect = Exception("Redis connection failed")

            result = await self.cache_manager.delete("test_key")
            assert result is False
            assert self.cache_manager._stats.errors == 1

    @pytest.mark.asyncio
    async def test_clear_namespace(self):
        """Test clearing all keys in a namespace."""
        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.keys.return_value = ["key1", "key2", "key3"]
            mock_client.delete.return_value = 3
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.clear_namespace("test_namespace")
            assert result == 3

    @pytest.mark.asyncio
    async def test_clear_namespace_no_keys(self):
        """Test clearing namespace with no keys."""
        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.keys.return_value = []
            mock_redis_client.return_value = mock_client

            result = await self.cache_manager.clear_namespace("empty_namespace")
            assert result == 0

    def test_get_stats(self):
        """Test getting cache statistics."""
        self.cache_manager._stats.hits = 10
        self.cache_manager._stats.misses = 5

        stats = self.cache_manager.get_stats()
        assert stats.hits == 10
        assert stats.misses == 5
        assert stats.hit_rate == 0.666666667  # 10/15


# Decorator tests removed as they don't exist in the current implementation


class TestCacheManagerSingleton:
    """Test cache manager singleton functionality."""

    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns same instance."""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        assert manager1 is manager2

    def test_cache_manager_is_instance(self):
        """Test that cache manager is correct type."""
        manager = get_cache_manager()
        assert isinstance(manager, CacheManager)


class TestCacheManagerMemoryManagement:
    """Test cache manager memory management."""

    def setup_method(self):
        """Set up test environment."""
        self.cache_manager = CacheManager()
        self.cache_manager._max_memory_items = 3  # Small limit for testing

    @pytest.mark.asyncio
    async def test_memory_cache_limit(self):
        """Test that memory cache respects size limit."""
        test_values = [
            {"data": "test1"},
            {"data": "test2"},
            {"data": "test3"},
            {"data": "test4"},  # This should cause eviction
        ]

        with patch.object(self.cache_manager, "get_redis_client") as mock_redis_client:
            mock_client = AsyncMock()
            mock_client.setex = AsyncMock()
            mock_redis_client.return_value = mock_client

            # Add items up to limit
            for i, value in enumerate(test_values):
                await self.cache_manager.set(f"key_{i}", value)

            # Memory cache should not exceed limit
            assert (
                len(self.cache_manager._memory_cache)
                <= self.cache_manager._max_memory_items
            )


if __name__ == "__main__":
    pytest.main([__file__])
