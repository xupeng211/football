"""
足球预测API服务

提供足球比赛结果预测的REST API接口
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from apps.api.routers import health, metrics, predictions
from apps.api.routers.metrics import REQUEST_COUNT, REQUEST_DURATION
from apps.api.services.prediction_service import prediction_service
from models.predictor import Predictor


class VersionResponse(BaseModel):
    """版本信息响应"""

    api_version: str
    model_version: str
    model_info: dict[str, Any]


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Trace-ID"] = trace_id

        REQUEST_DURATION.labels(
            method=request.method, endpoint=request.url.path
        ).observe(process_time)
        REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()

        print(
            f"trace_id={trace_id} method={request.method} "
            f"path='{request.url.path}' status_code={response.status_code} "
            f"process_time={process_time:.4f}s"
        )

        return response


logger = structlog.get_logger()
predictor = Predictor()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Loads all available models into memory on startup.
    """
    logger.info("Application startup: Loading models...")
    try:
        prediction_service.load_models()
        logger.info("Models loaded successfully.")
    except Exception as e:
        logger.error("Failed to load models during startup.", error=str(e))
    yield


# 创建FastAPI应用
app = FastAPI(
    title="足球预测API",
    description="足球比赛结果预测服务",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(LoggingMiddleware)
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(health.router)
app.include_router(metrics.router)


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
