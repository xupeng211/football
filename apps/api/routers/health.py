"""
健康检查路由
"""

from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.api.db import check_db_connection
from apps.api.model_registry import check_model_registry
from apps.api.prefect import check_prefect_connection_async
from apps.api.redis import check_redis_connection

logger = structlog.get_logger()
router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应模型"""

    status: str
    timestamp: datetime
    version: str
    components: dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    健康检查端点

    检查系统各组件的健康状态:
    - API服务状态
    - 数据库连接
    - Redis连接
    - 模型注册表
    """
    try:
        components = {}
        overall_status = "healthy"

        # 检查数据库连接
        db_ok, db_msg = check_db_connection()
        components["database"] = {
            "status": "healthy" if db_ok else "unhealthy",
            "message": db_msg,
        }

        # 检查Redis连接
        redis_ok, redis_msg = check_redis_connection()
        components["redis"] = {
            "status": "healthy" if redis_ok else "unhealthy",
            "message": redis_msg,
        }

        # 检查模型注册表
        model_ok, model_msg = check_model_registry()
        components["model_registry"] = {
            "status": "healthy" if model_ok else "unhealthy",
            "message": model_msg,
        }

        # 检查Prefect连接
        prefect_ok, prefect_msg = await check_prefect_connection_async()
        components["prefect"] = {
            "status": "healthy" if prefect_ok else "unhealthy",
            "message": prefect_msg,
        }

        # 如果任何组件不健康, 整体状态为不健康
        if any(comp.get("status") == "unhealthy" for comp in components.values()):
            overall_status = "unhealthy"

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="0.1.0",
            components=components,
        )

    except Exception as e:
        logger.error("健康检查失败", exc=str(e))
        raise HTTPException(status_code=503, detail="健康检查失败") from e
