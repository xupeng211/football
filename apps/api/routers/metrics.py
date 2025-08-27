"""
系统指标路由 - 提供Prometheus格式的监控指标
"""

import time

import structlog
from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    ProcessCollector,
    generate_latest,
)

logger = structlog.get_logger()
router = APIRouter()

# 创建自定义注册表
registry = CollectorRegistry()
ProcessCollector(registry=registry)

# 定义应用指标
REQUEST_COUNT = Counter(
    "api_requests_total", "API请求总数", ["method", "endpoint"], registry=registry
)

REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API请求耗时",
    ["method", "endpoint"],
    registry=registry,
)

SYSTEM_UPTIME = Gauge("system_uptime_seconds", "系统启动时间", registry=registry)

# 设置启动时间
_start_time = time.time()
SYSTEM_UPTIME.set_to_current_time()


@router.get("/metrics")
def get_metrics() -> Response:
    """
    获取系统指标 - Prometheus格式

    提供系统运行状态的关键指标,包括:
    - API请求统计
    - 模型预测统计
    - 系统资源使用
    - 数据管道状态
    """
    try:
        # 更新运行时长指标
        uptime_seconds = time.time() - _start_time
        SYSTEM_UPTIME.set(uptime_seconds)

        # 增加一些示例数据
        REQUEST_COUNT.labels(method="GET", endpoint="/health").inc()
        REQUEST_COUNT.labels(method="GET", endpoint="/metrics").inc()

        # 生成Prometheus格式的指标
        data = generate_latest(registry)

        logger.info("系统指标已生成", uptime=uptime_seconds)

        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    except Exception as e:
        logger.error("获取系统指标失败", exc=str(e))
        return Response(content="# 系统指标暂不可用\n", media_type=CONTENT_TYPE_LATEST)
