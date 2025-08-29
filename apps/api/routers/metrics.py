"""
Metrics router for Prometheus monitoring.
"""

import os
import time
from typing import Any

import structlog
from fastapi import APIRouter
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None

logger = structlog.get_logger(__name__)

router = APIRouter()

# Custom registry for testing to avoid conflicts
registry = CollectorRegistry()

# Prometheus metrics with custom registry
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint"],
    registry=registry,
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

SYSTEM_UPTIME = Counter(
    "system_uptime_seconds_total",
    "System uptime in seconds",
    registry=registry,
)

MEMORY_USAGE = Histogram(
    "memory_usage_bytes", "Memory usage in bytes", registry=registry
)


@router.get("/metrics")
async def get_metrics() -> Response:
    """
    Prometheus metrics endpoint.
    """
    # Update system metrics if psutil is available
    if psutil:
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            MEMORY_USAGE.observe(memory_info.rss)
        except Exception as e:
            logger.warning("Failed to record psutil metrics", error=str(e))

    # Generate metrics
    try:
        metrics_data = generate_latest(registry)
        return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error("Failed to generate Prometheus metrics", error=str(e))
        return Response(
            content=b"# An error occurred generating metrics\n",
            status_code=500,
            media_type=CONTENT_TYPE_LATEST,
        )


@router.get("/health/metrics")
async def get_health_metrics() -> dict[str, Any]:
    """
    Health-specific metrics endpoint.
    """
    if not psutil:
        return {"error": "psutil not installed, metrics unavailable"}

    try:
        process = psutil.Process(os.getpid())
        return {
            "memory_usage_mb": process.memory_info().rss / (1024 * 1024),
            "cpu_percent": process.cpu_percent(),
            "uptime_seconds": time.time() - process.create_time(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
        }
    except Exception as e:
        logger.error("Could not get health metrics", error=str(e))
        return {"error": "Failed to retrieve health metrics"}
