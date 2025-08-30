"""
Production-grade health check and monitoring system.

This module provides:
- Comprehensive health checks for all system components
- Metrics collection and monitoring
- Alerting and notification system
- Performance monitoring
"""

import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
from pydantic import BaseModel

from .config import get_settings
from .database import get_database_manager
from .logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentHealth(BaseModel):
    """Health status for a system component."""

    name: str
    status: HealthStatus
    response_time: float
    details: Dict[str, Any] = {}
    last_check: datetime
    error: Optional[str] = None


class SystemHealth(BaseModel):
    """Overall system health status."""

    status: HealthStatus
    components: List[ComponentHealth]
    timestamp: datetime
    uptime: float
    version: str


class HealthChecker:
    """Manages health checks for all system components."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.start_time = time.time()
        self._health_cache: Dict[str, ComponentHealth] = {}
        self._cache_ttl = 30  # Cache health results for 30 seconds

    async def check_database_health(self) -> ComponentHealth:
        """Check database connectivity and performance."""
        start_time = time.time()

        try:
            db_manager = get_database_manager()
            health_result = await db_manager.health_check()

            response_time = time.time() - start_time

            if health_result["status"] == "healthy":
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.UNHEALTHY

            return ComponentHealth(
                name="database",
                status=status,
                response_time=response_time,
                details=health_result,
                last_check=datetime.utcnow(),
            )

        except Exception as e:
            response_time = time.time() - start_time

            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                details={},
                last_check=datetime.utcnow(),
                error=str(e),
            )

    async def check_redis_health(self) -> ComponentHealth:
        """Check Redis connectivity and performance."""
        start_time = time.time()

        try:
            import redis.asyncio as redis

            redis_client = redis.from_url(self.settings.redis.url)

            # Test basic operations
            await redis_client.ping()
            await redis_client.set("health_check", "ok", ex=60)
            result = await redis_client.get("health_check")
            await redis_client.delete("health_check")

            response_time = time.time() - start_time

            status = HealthStatus.HEALTHY if result == b"ok" else HealthStatus.DEGRADED

            # Get Redis info
            info = await redis_client.info()

            await redis_client.close()

            return ComponentHealth(
                name="redis",
                status=status,
                response_time=response_time,
                details={
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory": info.get("used_memory_human"),
                    "uptime": info.get("uptime_in_seconds"),
                },
                last_check=datetime.utcnow(),
            )

        except ImportError:
            # Redis not available
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNKNOWN,
                response_time=0,
                details={"message": "Redis client not installed"},
                last_check=datetime.utcnow(),
            )
        except Exception as e:
            response_time = time.time() - start_time

            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                details={},
                last_check=datetime.utcnow(),
                error=str(e),
            )

    def check_system_resources(self) -> ComponentHealth:
        """Check system resource usage."""
        start_time = time.time()

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")

            # Network stats (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                }
            except:
                network_stats = {}

            response_time = time.time() - start_time

            # Determine health status based on resource usage
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY

            return ComponentHealth(
                name="system_resources",
                status=status,
                response_time=response_time,
                details={
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "used": memory.used,
                    },
                    "disk": {
                        "total": disk.total,
                        "free": disk.free,
                        "percent": disk.percent,
                        "used": disk.used,
                    },
                    "network": network_stats,
                },
                last_check=datetime.utcnow(),
            )

        except Exception as e:
            response_time = time.time() - start_time

            return ComponentHealth(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                details={},
                last_check=datetime.utcnow(),
                error=str(e),
            )

    async def check_model_registry(self) -> ComponentHealth:
        """Check model registry health."""
        start_time = time.time()

        try:
            from pathlib import Path

            model_path = Path(self.settings.ml.model_registry_path)

            if not model_path.exists():
                return ComponentHealth(
                    name="model_registry",
                    status=HealthStatus.UNHEALTHY,
                    response_time=time.time() - start_time,
                    details={"message": "Model registry path does not exist"},
                    last_check=datetime.utcnow(),
                    error="Model registry path not found",
                )

            # Count available models
            model_count = len(list(model_path.glob("**/model.pkl")))

            response_time = time.time() - start_time

            status = HealthStatus.HEALTHY if model_count > 0 else HealthStatus.DEGRADED

            return ComponentHealth(
                name="model_registry",
                status=status,
                response_time=response_time,
                details={"model_count": model_count, "registry_path": str(model_path)},
                last_check=datetime.utcnow(),
            )

        except Exception as e:
            response_time = time.time() - start_time

            return ComponentHealth(
                name="model_registry",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                details={},
                last_check=datetime.utcnow(),
                error=str(e),
            )

    async def check_external_apis(self) -> ComponentHealth:
        """Check external API connectivity."""
        start_time = time.time()

        try:
            import aiohttp

            # Test external APIs (example: football data API)
            external_apis = [
                {
                    "name": "football_api",
                    "url": "https://api.football-data.org/v4/competitions",
                    "timeout": 10,
                }
            ]

            api_results = []

            async with aiohttp.ClientSession() as session:
                for api in external_apis:
                    try:
                        async with session.get(
                            api["url"], timeout=api["timeout"]
                        ) as response:
                            api_results.append(
                                {
                                    "name": api["name"],
                                    "status_code": response.status,
                                    "response_time": response.headers.get(
                                        "X-Response-Time", "unknown"
                                    ),
                                    "healthy": 200 <= response.status < 300,
                                }
                            )
                    except Exception as api_error:
                        api_results.append(
                            {
                                "name": api["name"],
                                "error": str(api_error),
                                "healthy": False,
                            }
                        )

            response_time = time.time() - start_time

            # Determine overall status
            healthy_apis = sum(1 for api in api_results if api.get("healthy", False))
            total_apis = len(api_results)

            if healthy_apis == total_apis:
                status = HealthStatus.HEALTHY
            elif healthy_apis > 0:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            return ComponentHealth(
                name="external_apis",
                status=status,
                response_time=response_time,
                details={
                    "apis": api_results,
                    "healthy_count": healthy_apis,
                    "total_count": total_apis,
                },
                last_check=datetime.utcnow(),
            )

        except ImportError:
            return ComponentHealth(
                name="external_apis",
                status=HealthStatus.UNKNOWN,
                response_time=0,
                details={"message": "aiohttp not available"},
                last_check=datetime.utcnow(),
            )
        except Exception as e:
            response_time = time.time() - start_time

            return ComponentHealth(
                name="external_apis",
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                details={},
                last_check=datetime.utcnow(),
                error=str(e),
            )

    async def get_system_health(self, use_cache: bool = True) -> SystemHealth:
        """Get comprehensive system health status."""
        if use_cache:
            # Check if we have recent cached results
            now = datetime.utcnow()
            cached_results = []

            for component_name, health in self._health_cache.items():
                if (now - health.last_check).total_seconds() < self._cache_ttl:
                    cached_results.append(health)

            if len(cached_results) >= 4:  # We have most components cached
                components = cached_results
            else:
                components = await self._check_all_components()
        else:
            components = await self._check_all_components()

        # Update cache
        for component in components:
            self._health_cache[component.name] = component

        # Determine overall system status
        component_statuses = [comp.status for comp in components]

        if all(status == HealthStatus.HEALTHY for status in component_statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(status == HealthStatus.UNHEALTHY for status in component_statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in component_statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN

        uptime = time.time() - self.start_time

        return SystemHealth(
            status=overall_status,
            components=components,
            timestamp=datetime.utcnow(),
            uptime=uptime,
            version=self.settings.app_version,
        )

    async def _check_all_components(self) -> List[ComponentHealth]:
        """Check all system components."""
        tasks = [
            self.check_database_health(),
            self.check_redis_health(),
            self.check_model_registry(),
            self.check_external_apis(),
        ]

        # Add system resources check (synchronous)
        system_resources = self.check_system_resources()

        # Run async checks concurrently
        async_results = await asyncio.gather(*tasks, return_exceptions=True)

        components = [system_resources]

        for result in async_results:
            if isinstance(result, ComponentHealth):
                components.append(result)
            elif isinstance(result, Exception):
                self.logger.error("Health check failed", error=str(result))

        return components


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
