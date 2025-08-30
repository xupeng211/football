"""
Main application entry point for the football prediction system.

This module initializes the FastAPI application, configures middleware,
and sets up core components like logging, database, and caching.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


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


# Add health check endpoint
@app.get("/health", tags=["monitoring"])
async def health_check():
    """Perform system health check."""
    health_checker = get_health_checker()
    health_report = await health_checker.get_system_health()

    status_code = 200 if health_report.status == "healthy" else 503

    return JSONResponse(content=health_report.dict(), status_code=status_code)


# Add root endpoint
@app.get("/", tags=["general"])
async def root():
    """Root endpoint with application information."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


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
