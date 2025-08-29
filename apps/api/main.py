"""
足球预测API服务

提供足球比赛结果预测的REST API接口
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from apps.api.logging_config import configure_logging
from apps.api.routers import health, predictions
from apps.api.services.prediction_service import prediction_service
from models.predictor import Predictor

# Configure logging before creating any loggers
configure_logging()


class VersionResponse(BaseModel):
    """版本信息响应"""

    api_version: str
    model_version: str
    model_info: dict[str, Any]


logger = structlog.get_logger(__name__)
predictor = Predictor()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Loads models on startup and exposes Prometheus metrics.
    """
    logger.info("Application startup: Loading models...")
    try:
        prediction_service.load_models()
        logger.info("Models loaded successfully.")
    except Exception as e:
        logger.error("Failed to load models during startup.", error=str(e))

    # Instrument the app with Prometheus metrics
    Instrumentator().instrument(app).expose(app)
    yield


# 创建FastAPI应用
app = FastAPI(
    title="足球预测API",
    description="足球比赛结果预测服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(health.router)


@app.get("/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """获取版本信息"""
    # This should be enhanced to get the version from the loaded model service
    return VersionResponse(
        api_version="1.0.0",
        model_version="unknown",  # Placeholder
        model_info={},
    )


@app.get("/livez", tags=["health"])
async def livez() -> dict[str, str]:
    """Liveness probe to check if the application is running."""
    return {"status": "ok"}


@app.get("/readyz", tags=["health"])
async def readyz() -> dict[str, str]:
    """Readiness probe to check if the app is ready to serve traffic."""
    # This should check the actual prediction service status
    return {"status": "ok"}  # Placeholder


@app.get("/")
async def root() -> dict[str, str]:
    """根路径"""
    return {
        "message": "足球预测API服务",
        "docs": "/docs",
        "health": "/health",
        "version": "/version",
    }


if __name__ == "__main__":
    # 开发模式运行
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
