"""
Production-grade logging system with structured logging support.

This module provides:
- Structured JSON logging for production
- Human-readable logging for development
- Correlation ID tracking
- Performance monitoring
- Error tracking integration
"""

import json
import logging
import logging.handlers
import sys
import time
import traceback
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import structlog
from structlog.types import FilteringBoundLogger

from .config import get_settings

# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class CorrelationIDProcessor:
    """Add correlation ID to log records."""

    def __call__(
        self, logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        correlation_id = correlation_id_var.get()
        if correlation_id:
            event_dict["correlation_id"] = correlation_id

        user_id = user_id_var.get()
        if user_id:
            event_dict["user_id"] = user_id

        request_id = request_id_var.get()
        if request_id:
            event_dict["request_id"] = request_id

        return event_dict


class PerformanceProcessor:
    """Add performance metrics to log records."""

    def __call__(
        self, logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Add timestamp
        event_dict["timestamp"] = time.time()

        # Add performance data if available
        if "duration" in event_dict:
            event_dict["performance"] = {
                "duration_ms": event_dict["duration"] * 1000,
                "slow_query": event_dict["duration"] > 1.0,
            }

        return event_dict


class ErrorProcessor:
    """Enhanced error processing with stack traces."""

    def __call__(
        self, logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        if method_name in ("error", "exception", "critical"):
            # Add error details
            if "error" in event_dict:
                error = event_dict["error"]
                if isinstance(error, Exception):
                    event_dict["error_details"] = {
                        "type": error.__class__.__name__,
                        "message": str(error),
                        "traceback": traceback.format_exception(
                            type(error), error, error.__traceback__
                        ),
                    }
                    event_dict["error"] = str(error)

            # Add stack trace for exceptions
            if "exc_info" not in event_dict:
                event_dict["stack_trace"] = traceback.format_stack()

        return event_dict


class CustomJSONRenderer:
    """Custom JSON renderer with enhanced formatting."""

    def __call__(
        self, logger: FilteringBoundLogger, method_name: str, event_dict: Dict[str, Any]
    ) -> str:
        # Ensure required fields
        if "timestamp" not in event_dict:
            event_dict["timestamp"] = time.time()

        if "level" not in event_dict:
            event_dict["level"] = method_name.upper()

        # Add service information
        settings = get_settings()
        event_dict["service"] = {
            "name": settings.logging.service_name,
            "version": settings.logging.service_version,
            "environment": settings.environment.value,
        }

        return json.dumps(event_dict, default=str, ensure_ascii=False)


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Clear existing handlers
    logging.root.handlers.clear()

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        CorrelationIDProcessor(),
        PerformanceProcessor(),
        ErrorProcessor(),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.logging.format == "json":
        processors.append(CustomJSONRenderer())
        CustomJSONRenderer()
    else:
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )
        structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.logging.level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    handler: logging.Handler

    if settings.logging.file_path:
        # File logging with rotation
        log_path = Path(settings.logging.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=settings.logging.max_file_size,
            backupCount=settings.logging.backup_count,
            encoding="utf-8",
        )
    else:
        # Console logging
        handler = logging.StreamHandler(sys.stdout)

    # Set formatter
    if settings.logging.format == "json":
        formatter = logging.Formatter("%(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    handler.setLevel(getattr(logging, settings.logging.level))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.logging.level))
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> FilteringBoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for request tracking."""
    if correlation_id is None:
        correlation_id = str(uuid4())

    correlation_id_var.set(correlation_id)
    return correlation_id


def set_user_id(user_id: str) -> None:
    """Set user ID for request tracking."""
    user_id_var.set(user_id)


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID for request tracking."""
    if request_id is None:
        request_id = str(uuid4())

    request_id_var.set(request_id)
    return request_id


def clear_context() -> None:
    """Clear all context variables."""
    correlation_id_var.set(None)
    user_id_var.set(None)
    request_id_var.set(None)


class LoggingMiddleware:
    """Middleware for automatic request logging."""

    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Set request context
        request_id = set_request_id()
        correlation_id = set_correlation_id()

        start_time = time.time()

        # Log request start
        self.logger.info(
            "Request started",
            method=scope["method"],
            path=scope["path"],
            query_string=scope.get("query_string", b"").decode(),
            request_id=request_id,
            correlation_id=correlation_id,
        )

        try:
            await self.app(scope, receive, send)

            # Log successful request
            duration = time.time() - start_time
            self.logger.info("Request completed", duration=duration, status="success")

        except Exception as e:
            # Log failed request
            duration = time.time() - start_time
            self.logger.error(
                "Request failed", error=str(e), duration=duration, status="error"
            )
            raise
        finally:
            clear_context()


def log_performance(operation: str):
    """Decorator for logging operation performance."""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"{operation} completed",
                    operation=operation,
                    duration=duration,
                    function=func.__name__,
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    duration=duration,
                    function=func.__name__,
                    error=str(e),
                )
                raise

        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"{operation} completed",
                    operation=operation,
                    duration=duration,
                    function=func.__name__,
                )

                return result
            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"{operation} failed",
                    operation=operation,
                    duration=duration,
                    function=func.__name__,
                    error=str(e),
                )
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
