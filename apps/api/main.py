"""
足球赛果预测系统 - API主入口
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.core.logging import setup_logging
from apps.api.core.settings import settings
from apps.api.routers import health, metrics, predictions

# 配置已导入

# 设置日志
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    logger.info("🚀 启动足球赛果预测系统API")

    # TODO: 初始化数据库连接池
    # TODO: 初始化模型注册表
    # TODO: 初始化Redis连接
    # TODO: 启动后台任务

    yield

    # TODO: 清理资源
    logger.info("🛑 关闭足球赛果预测系统API")


# 创建FastAPI应用
app = FastAPI(
    title="足球赛果预测系统",
    description="基于机器学习的足球比赛结果预测API",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error("未处理的异常", exc=str(exc), path=str(request.url))
    return JSONResponse(status_code=500, content={"detail": "内部服务器错误"})


# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["健康检查"])
app.include_router(predictions.router, prefix="/api/v1", tags=["预测"])
app.include_router(metrics.router, prefix="/api/v1", tags=["监控"])


@app.get("/")
async def root():
    """根路径"""
    return {"message": "足球赛果预测系统API", "version": "0.1.0", "status": "running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.api.main:app",
        host=settings.api_host,
        port=settings.app_port,
        reload=settings.api_debug,
        log_level="info",
    )
