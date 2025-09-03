"""
Centralized exception handling for the football prediction system.

This module provides:
- Custom exception hierarchy
- Error codes and messages
- Exception handlers for different contexts
- Error reporting and alerting
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""

    # General errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"

    # Database errors
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    DATABASE_INTEGRITY_ERROR = "DATABASE_INTEGRITY_ERROR"
    DATABASE_TIMEOUT_ERROR = "DATABASE_TIMEOUT_ERROR"

    # ML/Model errors
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_LOADING_ERROR = "MODEL_LOADING_ERROR"
    PREDICTION_ERROR = "PREDICTION_ERROR"
    TRAINING_ERROR = "TRAINING_ERROR"
    FEATURE_EXTRACTION_ERROR = "FEATURE_EXTRACTION_ERROR"

    # Data pipeline errors
    DATA_INGESTION_ERROR = "DATA_INGESTION_ERROR"
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"
    DATA_TRANSFORMATION_ERROR = "DATA_TRANSFORMATION_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"

    # Business logic errors
    INVALID_MATCH_DATA = "INVALID_MATCH_DATA"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    PREDICTION_UNAVAILABLE = "PREDICTION_UNAVAILABLE"


class BaseApplicationError(Exception):
    """Base exception class for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "type": self.__class__.__name__,
        }

    def __str__(self) -> str:
        return f"{self.error_code.value}: {self.message}"


class ValidationError(BaseApplicationError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details or {},
        )
        if field:
            self.details["field"] = field


class NotFoundError(BaseApplicationError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource: str,
        identifier: str | int,
        details: dict[str, Any] | None = None,
    ):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            details=details or {},
        )
        self.details["resource"] = resource
        self.details["identifier"] = str(identifier)


class UnauthorizedError(BaseApplicationError):
    """Raised when authentication is required but not provided."""

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message, error_code=ErrorCode.UNAUTHORIZED, details=details
        )


class ForbiddenError(BaseApplicationError):
    """Raised when user lacks permission for the requested action."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message, error_code=ErrorCode.FORBIDDEN, details=details
        )


class RateLimitError(BaseApplicationError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message, error_code=ErrorCode.RATE_LIMITED, details=details
        )


class DatabaseError(BaseApplicationError):
    """Base class for database-related errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        query: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)
        if query:
            self.details["query"] = query


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Database connection failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
            details=details,
        )


class DatabaseQueryError(DatabaseError):
    """Raised when database query execution fails."""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_QUERY_ERROR,
            query=query,
            details=details,
        )


class ModelError(BaseApplicationError):
    """Base class for ML model-related errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        model_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)
        if model_name:
            self.details["model_name"] = model_name


class ModelNotFoundError(ModelError):
    """Raised when a requested model is not found."""

    def __init__(self, model_name: str, version: str | None = None):
        message = f"Model '{model_name}'"
        if version:
            message += f" version '{version}'"
        message += " not found"

        details = {"model_name": model_name}
        if version:
            details["version"] = version

        super().__init__(
            message=message,
            error_code=ErrorCode.MODEL_NOT_FOUND,
            details=details,
        )


class PredictionError(ModelError):
    """Raised when model prediction fails."""

    def __init__(
        self,
        message: str = "Prediction failed",
        model_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.PREDICTION_ERROR,
            model_name=model_name,
            details=details,
        )


class DataPipelineError(BaseApplicationError):
    """Base class for data pipeline errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        pipeline_stage: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)
        if pipeline_stage:
            self.details["pipeline_stage"] = pipeline_stage


class DataIngestionError(DataPipelineError):
    """Raised when data ingestion fails."""

    def __init__(
        self,
        message: str,
        source: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATA_INGESTION_ERROR,
            details=details,
        )
        if source:
            self.details["source"] = source


class ExternalAPIError(DataPipelineError):
    """Raised when external API calls fail."""

    def __init__(
        self,
        message: str,
        api_name: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            details=details or {},
        )
        if api_name:
            self.details["api_name"] = api_name
        if status_code:
            self.details["status_code"] = status_code


class BusinessLogicError(BaseApplicationError):
    """Base class for business logic errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        context: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)
        if context:
            self.details["context"] = context


class InsufficientDataError(BusinessLogicError):
    """Raised when there's insufficient data for processing."""

    def __init__(
        self,
        message: str = "Insufficient data for processing",
        required_count: int | None = None,
        actual_count: int | None = None,
    ):
        details = {}
        if required_count is not None:
            details["required_count"] = required_count
        if actual_count is not None:
            details["actual_count"] = actual_count

        super().__init__(
            message=message, error_code=ErrorCode.INSUFFICIENT_DATA, details=details
        )


def handle_database_exception(exc: Exception) -> DatabaseError:
    """Convert database exceptions to application exceptions."""
    import sqlalchemy.exc as sa_exc

    if isinstance(exc, sa_exc.DisconnectionError):
        return DatabaseConnectionError(
            "Database connection lost", details={"original_error": str(exc)}
        )
    if isinstance(exc, sa_exc.TimeoutError):
        return DatabaseError(
            "Database query timeout",
            ErrorCode.DATABASE_TIMEOUT_ERROR,
            details={"original_error": str(exc)},
        )
    if isinstance(exc, sa_exc.IntegrityError):
        return DatabaseError(
            "Database integrity constraint violation",
            ErrorCode.DATABASE_INTEGRITY_ERROR,
            details={"original_error": str(exc)},
        )
    if isinstance(exc, sa_exc.SQLAlchemyError):
        return DatabaseQueryError(
            "Database query failed", details={"original_error": str(exc)}
        )
    return DatabaseError(
        "Unknown database error",
        ErrorCode.DATABASE_CONNECTION_ERROR,
        details={"original_error": str(exc)},
    )


def handle_external_api_exception(
    exc: Exception, api_name: str | None = None
) -> ExternalAPIError:
    """Convert external API exceptions to application exceptions."""
    import requests.exceptions as req_exc

    if isinstance(exc, req_exc.ConnectionError):
        return ExternalAPIError(
            "Failed to connect to external API",
            api_name=api_name,
            details={"original_error": str(exc)},
        )
    if isinstance(exc, req_exc.Timeout):
        return ExternalAPIError(
            "External API request timeout",
            api_name=api_name,
            details={"original_error": str(exc)},
        )
    if isinstance(exc, req_exc.HTTPError):
        status_code = (
            getattr(exc.response, "status_code", None)
            if hasattr(exc, "response")
            else None
        )
        return ExternalAPIError(
            "External API HTTP error",
            api_name=api_name,
            status_code=status_code,
            details={"original_error": str(exc)},
        )
    return ExternalAPIError(
        "Unknown external API error",
        api_name=api_name,
        details={"original_error": str(exc)},
    )
