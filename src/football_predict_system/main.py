"""
Main application entry point for the football prediction system.

This module initializes the FastAPI application, configures middleware,
and sets up core components like logging, database, and caching.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from .api.v1.endpoints import router as api_v1_router
from .core.cache import get_cache_manager
from .core.config import get_settings
from .core.database import get_database_manager
from .core.exceptions import BaseApplicationError
from .core.health import get_health_checker
from .core.logging import get_logger, setup_logging
from .core.security import SecurityHeaders

# Initialize core components
setup_logging()
settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    logger.info("Application startup sequence initiated")

    # Initialize database connections
    db_manager = get_database_manager()
    _ = db_manager.get_engine()  # Initialize sync engine
    _ = db_manager.get_async_engine()  # Initialize async engine

    # Initialize cache connections
    cache_manager = await get_cache_manager()
    _ = await cache_manager.get_redis_client()

    # Initialize Prometheus metrics
    if hasattr(app.state, "instrumentator"):
        app.state.instrumentator.expose(app)
        logger.info("Prometheus metrics endpoint exposed at /metrics")

    logger.info("Application startup complete")
    yield

    # Cleanup resources
    logger.info("Application shutdown sequence initiated")
    await db_manager.close()
    await cache_manager.close()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    # Add OpenAPI documentation configuration here
    openapi_url="/openapi.json",  # Standard OpenAPI URL
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "general", "description": "General endpoints"},
        {"name": "monitoring", "description": "Health and monitoring endpoints"},
        {"name": "predictions", "description": "Prediction endpoints"},
        {"name": "models", "description": "Model management endpoints"},
    ],
)

# Configure Prometheus monitoring
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/health/ready", "/health/live", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrument the FastAPI app
instrumentator.instrument(app)

# Store instrumentator in app state for lifespan access
app.state.instrumentator = instrumentator


# Configure middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=settings.api.cors_credentials,
    allow_methods=settings.api.cors_methods,
    allow_headers=settings.api.cors_headers,
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    headers = SecurityHeaders.get_security_headers()
    for key, value in headers.items():
        response.headers[key] = value
    return response


# Configure exception handlers
@app.exception_handler(BaseApplicationError)
async def application_exception_handler(request: Request, exc: BaseApplicationError):
    """Handle custom application exceptions."""
    logger.error(
        "Application error occurred",
        error_code=exc.error_code.value,
        message=exc.message,
        details=exc.details,
    )
    return JSONResponse(
        status_code=400,  # Default to 400, can be customized
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.critical("An unexpected error occurred", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred",
            "details": {"error_type": exc.__class__.__name__},
        },
    )


# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")


# Health check endpoints - Production ready monitoring
@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Comprehensive system health check.

    Returns detailed health status of all system components including:
    - Database connectivity
    - Redis cache
    - External APIs
    - System resources
    - Model registry
    """
    try:
        health_checker = get_health_checker()
        health_report = await health_checker.get_system_health()

        # In development environment, be more lenient about unhealthy components
        is_dev_env = settings.environment.value in ["development", "testing"]

        if health_report.status == "healthy":
            status_code = 200
        elif health_report.status == "degraded":
            status_code = 200  # Degraded is acceptable
        elif is_dev_env:
            # In dev environment, return 200 even if some components are unhealthy
            status_code = 200
        else:
            status_code = 503

        return JSONResponse(
            content=health_report.model_dump(mode="json"), status_code=status_code
        )
    except (ImportError, ValueError, ConnectionError) as e:
        logger.error("Health check failed", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "version": settings.app_version,
            },
        )


@app.get("/health/ready", tags=["monitoring"])
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.

    Checks if the service is ready to accept traffic by verifying:
    - Database connectivity
    - Cache availability
    - Essential dependencies

    Returns 200 if ready, 503 if not ready.
    """
    try:
        # Check critical dependencies only
        db_manager = get_database_manager()
        cache_manager = await get_cache_manager()

        # Quick health checks for readiness
        db_check = await db_manager.health_check()

        # Try to ping Redis
        redis_client = await cache_manager.get_redis_client()
        cache_healthy = True
        try:
            await redis_client.ping()
        except Exception:
            cache_healthy = False

        # Service is ready if both critical services are healthy
        if db_check.get("status") == "healthy" and cache_healthy:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {"database": "healthy", "cache": "healthy"},
            }
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "database": (
                        "healthy"
                        if db_check.get("status") == "healthy"
                        else "unhealthy"
                    ),
                    "cache": "healthy" if cache_healthy else "unhealthy",
                },
            },
        )
    except Exception as e:
        logger.warning("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            },
        )


@app.get("/health/live", tags=["monitoring"])
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Simple endpoint to verify the application process is alive and responding.
    This should only fail if the application is completely unresponsive.

    Always returns 200 unless the process is dead.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (
            __import__("time").time()
            - app.state.__dict__.get("start_time", __import__("time").time())
        ),
        "version": settings.app_version,
    }


# Add root endpoint
@app.get("/", tags=["general"])
async def root():
    """Root endpoint with application information."""
    return {
        "app_name": settings.app_name,
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment.value,
        "timestamp": datetime.utcnow().isoformat(),
        "docs_url": "/docs",
        "health_url": "/health",
    }


# Add version endpoint for compatibility
@app.get("/version", tags=["general"])
async def get_version():
    """Get application version information."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",  # 添加API版本
        "model_version": settings.ml.default_model_version or "1.0.0",
        "model_info": {
            "registry_path": settings.ml.model_registry_path,
            "default_version": settings.ml.default_model_version or "1.0.0",
        },
        "environment": settings.environment.value,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Add livez endpoint for compatibility
@app.get("/livez", tags=["monitoring"])
async def livez():
    """Liveness probe endpoint (alias for /health/live)."""
    return await liveness_check()


# Example of how to run the application with uvicorn
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "football_predict_system.main:app",
#         host=settings.api.host,
#         port=settings.api.port,
#         reload=settings.api.reload,
#         workers=settings.api.workers,
#         log_level=settings.api.log_level.lower()
#     )
