"""
足球预测API服务

提供足球比赛结果预测的REST API接口
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI

# AI-Fix-Enhancement: Import OpenTelemetry modules
from opentelemetry import trace
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from apps.api.db import check_db_connection_async
from apps.api.logging_config import configure_logging
from apps.api.middleware import LoggingMiddleware
from apps.api.routers import health, predictions
from apps.api.services.prediction_service import prediction_service
from models.predictor import Predictor

# AI-Fix-Enhancement: Configure logging and OpenTelemetry
# This should be called once at the beginning of the application startup.
configure_logging()

# Initialize OpenTelemetry
resource = Resource.create({"service.name": "football-predict-api"})
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

AsyncPGInstrumentor().instrument()
RedisInstrumentor().instrument()


class VersionResponse(BaseModel):
    """版本信息响应"""

    api_version: str
    model_version: str
    model_info: dict[str, Any]


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Loads models on startup and exposes Prometheus metrics.
    """
    logger.info("Application startup: Checking database connection...")
    db_ok, db_msg = await check_db_connection_async()
    if not db_ok:
        logger.error("Database connection failed during startup.", message=db_msg)
        # Depending on the desired behavior, you might want to exit the application
        # raise RuntimeError("Failed to connect to the database on startup.")
    else:
        logger.info("Database connection successful.")

    logger.info("Application startup: Loading models...")
    predictor = None
    try:
        # The Predictor object is now initialized here, during startup.
        predictor = Predictor()
        prediction_service.set_predictor(predictor)
        logger.info("Models loaded and predictor set successfully.")
    except Exception as e:
        logger.error("Failed to load models during startup.", error=str(e))
        # Create a fallback predictor to prevent service failures
        predictor = Predictor()
        prediction_service.set_predictor(predictor)

    app.state.predictor = predictor
    yield


# 创建FastAPI应用
app = FastAPI(
    title="足球预测API",
    description="足球比赛结果预测服务",
    version="1.0.0",
    lifespan=lifespan,
)
# Add logging middleware
# AI-Fix-Enhancement: Instrument FastAPI app with OpenTelemetry
# This should be one of the first middlewares to capture the full request lifecycle.
FastAPIInstrumentor.instrument_app(app)

# Add logging middleware
app.add_middleware(LoggingMiddleware)


# Instrument the app with Prometheus metrics
Instrumentator().instrument(app).expose(app)

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
