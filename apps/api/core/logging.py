"""
结构化日志配置
"""

import logging
import sys
from typing import Any

import structlog

from apps.api.core.settings import settings


def setup_logging() -> None:
    """设置结构化日志"""

    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # 配置structlog
    if settings.log_format == "json":
        renderer: structlog.typing.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger_with_trace(trace_id: str) -> Any:
    """获取带trace_id的日志器"""
    return structlog.get_logger().bind(trace_id=trace_id)


def log_api_request(method: str, path: str, trace_id: str, **kwargs: Any) -> None:
    """记录API请求日志"""
    logger = get_logger_with_trace(trace_id)
    logger.info("API请求", method=method, path=path, **kwargs)


def log_api_response(
    method: str, path: str, status_code: int, duration_ms: float, trace_id: str
) -> None:
    """记录API响应日志"""
    logger = get_logger_with_trace(trace_id)
    logger.info(
        "API响应", method=method, path=path, status_code=status_code, duration_ms=duration_ms
    )
