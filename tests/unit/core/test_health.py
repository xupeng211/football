"""Tests for core health module."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from football_predict_system.core.health import (
    ComponentHealth,
    HealthChecker,
    HealthStatus,
    get_health_checker,
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test that health status enum has expected values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.DEGRADED == "degraded"


class TestComponentHealth:
    """Test ComponentHealth model."""

    def test_component_health_creation(self):
        """Test creating a ComponentHealth instance."""
        health = ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Connection successful",
            details={"latency_ms": 50}
        )

        assert health.name == "database"
        assert health.status == HealthStatus.HEALTHY
        assert health.message == "Connection successful"
        assert health.details["latency_ms"] == 50

    def test_component_health_unhealthy(self):
        """Test creating an unhealthy ComponentHealth."""
        health = ComponentHealth(
            name="cache",
            status=HealthStatus.UNHEALTHY,
            message="Redis connection failed",
            details={"error": "Connection timeout"}
        )

        assert health.status == HealthStatus.UNHEALTHY
        assert "failed" in health.message


class TestHealthChecker:
    """Test HealthChecker class."""

    @pytest.fixture
    def health_checker(self):
        """Create a HealthChecker instance."""
        with patch('football_predict_system.core.health.get_settings') as mock_settings:
            mock_settings.return_value.health_check_timeout = 30
            return HealthChecker()

    def test_health_checker_initialization(self, health_checker):
        """Test HealthChecker initialization."""
        assert health_checker is not None
        assert hasattr(health_checker, 'settings')

    @pytest.mark.asyncio
    async def test_check_database_health_success(self, health_checker):
        """Test successful database health check."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = True

        with patch(
            'football_predict_system.core.health.get_database_manager',
            return_value=mock_db_manager
        ):
            result = await health_checker.check_database_health()

            assert result.name == "database"
            assert result.status == HealthStatus.HEALTHY
            assert "operational" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_database_health_failure(self, health_checker):
        """Test failed database health check."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = False

        with patch(
            'football_predict_system.core.health.get_database_manager',
            return_value=mock_db_manager
        ):
            result = await health_checker.check_database_health()

            assert result.name == "database"
            assert result.status == HealthStatus.UNHEALTHY
            assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_database_health_exception(self, health_checker):
        """Test database health check with exception."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.side_effect = Exception("Connection error")

        with patch(
            'football_predict_system.core.health.get_database_manager',
            return_value=mock_db_manager
        ):
            result = await health_checker.check_database_health()

            assert result.name == "database"
            assert result.status == HealthStatus.UNHEALTHY
            assert "error" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_cache_health_success(self, health_checker):
        """Test successful cache health check."""
        mock_cache_manager = AsyncMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.ping.return_value = True
        mock_cache_manager.get_redis_client.return_value = mock_redis_client

        with patch(
            'football_predict_system.core.health.get_cache_manager',
            return_value=mock_cache_manager
        ):
            result = await health_checker.check_cache_health()

            assert result.name == "cache"
            assert result.status == HealthStatus.HEALTHY
            assert "operational" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_cache_health_failure(self, health_checker):
        """Test failed cache health check."""
        mock_cache_manager = AsyncMock()
        mock_redis_client = AsyncMock()
        mock_redis_client.ping.side_effect = Exception("Redis not available")
        mock_cache_manager.get_redis_client.return_value = mock_redis_client

        with patch(
            'football_predict_system.core.health.get_cache_manager',
            return_value=mock_cache_manager
        ):
            result = await health_checker.check_cache_health()

            assert result.name == "cache"
            assert result.status == HealthStatus.UNHEALTHY
            assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_all_components_healthy(self, health_checker):
        """Test checking all components when all are healthy."""
        # Mock all components as healthy
        with patch.object(
            health_checker, 'check_database_health'
        ) as mock_db_check:
            with patch.object(
                health_checker, 'check_cache_health'
            ) as mock_cache_check:
                mock_db_check.return_value = ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="OK"
                )
                mock_cache_check.return_value = ComponentHealth(
                    name="cache",
                    status=HealthStatus.HEALTHY,
                    message="OK"
                )

                result = await health_checker.check_all_components()

                assert len(result) == 2
                assert all(comp.status == HealthStatus.HEALTHY for comp in result)

    @pytest.mark.asyncio
    async def test_check_all_components_some_unhealthy(self, health_checker):
        """Test checking all components when some are unhealthy."""
        with patch.object(
            health_checker, 'check_database_health'
        ) as mock_db_check:
            with patch.object(
                health_checker, 'check_cache_health'
            ) as mock_cache_check:
                mock_db_check.return_value = ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="OK"
                )
                mock_cache_check.return_value = ComponentHealth(
                    name="cache",
                    status=HealthStatus.UNHEALTHY,
                    message="Failed"
                )

                result = await health_checker.check_all_components()

                assert len(result) == 2
                db_health = next(comp for comp in result if comp.name == "database")
                cache_health = next(comp for comp in result if comp.name == "cache")

                assert db_health.status == HealthStatus.HEALTHY
                assert cache_health.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_get_overall_status_all_healthy(self, health_checker):
        """Test getting overall status when all components are healthy."""
        components = [
            ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="OK"
            ),
            ComponentHealth(
                name="cache",
                status=HealthStatus.HEALTHY,
                message="OK"
            )
        ]

        status = health_checker.get_overall_status(components)
        assert status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_get_overall_status_some_unhealthy(self, health_checker):
        """Test getting overall status when some components are unhealthy."""
        components = [
            ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="OK"
            ),
            ComponentHealth(
                name="cache",
                status=HealthStatus.UNHEALTHY,
                message="Failed"
            )
        ]

        status = health_checker.get_overall_status(components)
        assert status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_get_overall_status_degraded(self, health_checker):
        """Test getting overall status when components are degraded."""
        components = [
            ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="OK"
            ),
            ComponentHealth(
                name="cache",
                status=HealthStatus.DEGRADED,
                message="Slow"
            )
        ]

        status = health_checker.get_overall_status(components)
        assert status == HealthStatus.DEGRADED


class TestHealthCheckerSingleton:
    """Test HealthChecker singleton pattern."""

    @patch('football_predict_system.core.health.HealthChecker')
    def test_get_health_checker_singleton(self, mock_health_checker_class):
        """Test that get_health_checker returns singleton instance."""
        mock_instance = Mock()
        mock_health_checker_class.return_value = mock_instance

        # First call should create instance
        checker1 = get_health_checker()
        assert checker1 == mock_instance

        # Second call should return same instance
        checker2 = get_health_checker()
        assert checker2 == mock_instance

        # Should only create one instance
        mock_health_checker_class.assert_called_once()


class TestHealthCheckerIntegration:
    """Test HealthChecker integration scenarios."""

    @pytest.mark.asyncio
    async def test_health_check_with_timeout(self):
        """Test health check with timeout handling."""
        with patch('football_predict_system.core.health.get_settings') as mock_settings:
            mock_settings.return_value.health_check_timeout = 1  # 1 second timeout
            health_checker = HealthChecker()

            # Mock a slow database check
            mock_db_manager = AsyncMock()

            async def slow_health_check():
                import asyncio
                await asyncio.sleep(2)  # Longer than timeout
                return True

            mock_db_manager.health_check = slow_health_check

            with patch(
                'football_predict_system.core.health.get_database_manager',
                return_value=mock_db_manager
            ):
                result = await health_checker.check_database_health()

                # Should handle timeout gracefully
                assert result.name == "database"
                # The exact behavior depends on implementation
                assert result.status in [
                    HealthStatus.UNHEALTHY,
                    HealthStatus.DEGRADED
                ]
