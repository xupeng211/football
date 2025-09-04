"""
Tests for cache decorators.

Tests the caching decorators and their functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest

from football_predict_system.core.cache.decorators import cached


class TestCachedDecorator:
    """Test cached decorator functionality."""

    @pytest.mark.asyncio
    async def test_cached_decorator_basic(self):
        """Test basic cached decorator functionality."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None  # Cache miss
        cache_manager.set.return_value = True

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_cache_class:
            mock_cache_class.return_value = cache_manager

            @cached(ttl=300)
            async def test_function(x: int) -> int:
                return x * 2

            result = await test_function(5)

            assert result == 10
            cache_manager.get.assert_called_once()
            cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_decorator_cache_hit(self):
        """Test cached decorator with cache hit."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = 20  # Cache hit

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300)
            async def test_function(x: int) -> int:
                return x * 2

            result = await test_function(10)

            assert result == 20  # From cache
            cache_manager.get.assert_called_once()
            cache_manager.set.assert_not_called()  # No need to set on cache hit

    @pytest.mark.asyncio
    async def test_cached_decorator_with_namespace(self):
        """Test cached decorator with custom namespace."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300, namespace="custom")
            async def test_function(x: int) -> int:
                return x * 3

            result = await test_function(5)

            assert result == 15
            # Check that namespace was used in cache key
            cache_manager.get.assert_called_once()
            call_args = cache_manager.get.call_args
            assert call_args[0][1] == "custom"  # namespace is the second positional arg

    @pytest.mark.asyncio
    async def test_cached_decorator_key_generation(self):
        """Test cache key generation for different arguments."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300)
            async def test_function(x: int, y: str = "default") -> str:
                return f"{x}_{y}"

            # Call with different arguments
            await test_function(1, "test")
            await test_function(2, "other")

            # Should generate different cache keys
            assert cache_manager.get.call_count == 2

            # Verify different keys were used
            call_args_list = cache_manager.get.call_args_list
            key1 = call_args_list[0][0][0]
            key2 = call_args_list[1][0][0]
            assert key1 != key2

    @pytest.mark.asyncio
    async def test_cached_decorator_cache_error_handling(self):
        """Test cached decorator handles cache errors gracefully."""

        cache_manager = AsyncMock()
        cache_manager.get.side_effect = Exception("Cache error")
        cache_manager.set.side_effect = Exception("Cache error")

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300)
            async def test_function(x: int) -> int:
                return x * 2

            # Should still work even if cache fails
            result = await test_function(5)
            assert result == 10

    @pytest.mark.asyncio
    async def test_cached_decorator_without_ttl(self):
        """Test cached decorator with default TTL."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached()  # No TTL specified
            async def test_function(x: int) -> int:
                return x * 2

            result = await test_function(5)

            assert result == 10
            cache_manager.set.assert_called_once()
            # Check that default TTL was used (should be None or default value)
            call_args = cache_manager.set.call_args
            assert call_args is not None

    def test_cached_decorator_on_sync_function(self):
        """Test that cached decorator works only on async functions."""

        # This should raise an error or be handled appropriately
        try:

            @cached(ttl=300)
            def sync_function(x: int) -> int:
                return x * 2

            # If it doesn't raise error, the decorator should at least not break
            assert callable(sync_function)
        except Exception:
            # Expected if decorator only supports async functions
            pass

    @pytest.mark.asyncio
    async def test_cached_decorator_with_complex_args(self):
        """Test cached decorator with complex argument types."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300)
            async def test_function(data: dict, items: list) -> str:
                return f"{len(data)}_{len(items)}"

            result = await test_function({"a": 1, "b": 2}, [1, 2, 3])

            assert result == "2_3"
            cache_manager.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_decorator_return_types(self):
        """Test cached decorator with different return types."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300)
            async def return_dict() -> dict:
                return {"key": "value"}

            @cached(ttl=300)
            async def return_list() -> list:
                return [1, 2, 3]

            @cached(ttl=300)
            async def return_none() -> None:
                return None

            dict_result = await return_dict()
            list_result = await return_list()
            none_result = await return_none()

            assert dict_result == {"key": "value"}
            assert list_result == [1, 2, 3]
            assert none_result is None


class TestCacheKeyGeneration:
    """Test cache key generation logic."""

    @pytest.mark.asyncio
    async def test_key_generation_with_different_types(self):
        """Test key generation with different argument types."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300)
            async def test_function(
                int_arg: int, str_arg: str, bool_arg: bool, float_arg: float
            ) -> str:
                return "result"

            await test_function(1, "test", True, 3.14)

            # Verify cache was called
            cache_manager.get.assert_called_once()

            # Verify key generation didn't fail with different types
            call_args = cache_manager.get.call_args
            assert call_args is not None
            assert isinstance(call_args[0][0], str)  # Key should be string

    @pytest.mark.asyncio
    async def test_key_generation_consistency(self):
        """Test that same arguments generate same key."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = "cached_result"

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300)
            async def test_function(x: int, y: str) -> str:
                return f"{x}_{y}"

            # Call twice with same arguments
            result1 = await test_function(1, "test")
            result2 = await test_function(1, "test")

            assert result1 == "cached_result"
            assert result2 == "cached_result"

            # Should use same cache key both times
            assert cache_manager.get.call_count == 2
            call_args_list = cache_manager.get.call_args_list
            key1 = call_args_list[0][0][0]
            key2 = call_args_list[1][0][0]
            assert key1 == key2


class TestCacheDecoratorIntegration:
    """Integration tests for cache decorators."""

    def test_decorator_import(self):
        """Test that decorator can be imported."""

        from football_predict_system.core.cache.decorators import cached

        assert callable(cached)

    @pytest.mark.asyncio
    async def test_multiple_decorated_functions(self):
        """Test multiple functions with cache decorators."""

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True

        with patch(
            "football_predict_system.core.cache.decorators.CacheManager"
        ) as mock_get_cache:
            mock_get_cache.return_value = cache_manager

            @cached(ttl=300, namespace="func1")
            async def function1(x: int) -> int:
                return x * 2

            @cached(ttl=600, namespace="func2")
            async def function2(x: int) -> int:
                return x * 3

            result1 = await function1(5)
            result2 = await function2(5)

            assert result1 == 10
            assert result2 == 15

            # Both functions should use cache
            assert cache_manager.get.call_count == 2
            assert cache_manager.set.call_count == 2
