import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and add a trace_id."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Clear context variables for the new request
        structlog.contextvars.clear_contextvars()

        # Generate a unique trace_id for the request
        trace_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            path=request.url.path,
            method=request.method,
            client_host=request.client.host if request.client else None,
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = trace_id
            status_code = response.status_code
        except Exception as e:
            logger.exception("Unhandled exception during request processing")
            status_code = 500
            response = Response("Internal Server Error", status_code=status_code)
            raise e
        finally:
            end_time = time.perf_counter()
            processing_time = (end_time - start_time) * 1000  # in milliseconds

            structlog.contextvars.bind_contextvars(status_code=status_code)
            logger.info(
                "Request completed",
                processing_time_ms=f"{processing_time:.2f}",
            )

        return response
