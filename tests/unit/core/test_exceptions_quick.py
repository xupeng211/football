"""
Quick tests for core exceptions module.

Focused on high-coverage simple tests.
"""

import pytest

from football_predict_system.core.exceptions import (
    BaseApplicationError,
    DatabaseConnectionError,
    ErrorCode,
    ModelNotFoundError,
    NotFoundError,
    PredictionError,
    UnauthorizedError,
    ValidationError,
)


class TestErrorCode:
    """Test ErrorCode enum."""

    def test_error_codes_exist(self):
        """Test error codes exist and have correct values."""
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.MODEL_NOT_FOUND == "MODEL_NOT_FOUND"
        assert ErrorCode.DATABASE_CONNECTION_ERROR == "DATABASE_CONNECTION_ERROR"


class TestBaseApplicationError:
    """Test BaseApplicationError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = BaseApplicationError("Test error", ErrorCode.INTERNAL_SERVER_ERROR)
        assert error.message == "Test error"
        assert error.error_code == ErrorCode.INTERNAL_SERVER_ERROR

    def test_to_dict(self):
        """Test to_dict method."""
        error = BaseApplicationError(
            "Test", ErrorCode.VALIDATION_ERROR, details={"key": "value"}
        )
        result = error.to_dict()
        assert result["error_code"] == "VALIDATION_ERROR"
        assert result["message"] == "Test"
        assert result["details"]["key"] == "value"

    def test_str_representation(self):
        """Test string representation."""
        error = BaseApplicationError("Test", ErrorCode.NOT_FOUND)
        assert "NOT_FOUND: Test" in str(error)


class TestValidationError:
    """Test ValidationError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.error_code == ErrorCode.VALIDATION_ERROR

    def test_init_with_field(self):
        """Test initialization with field."""
        error = ValidationError("Required field", field="username")
        assert error.details["field"] == "username"


class TestNotFoundError:
    """Test NotFoundError class."""

    def test_init_string_id(self):
        """Test initialization with string identifier."""
        error = NotFoundError("User", "john")
        assert "User with identifier 'john' not found" in error.message
        assert error.details["resource"] == "User"
        assert error.details["identifier"] == "john"

    def test_init_int_id(self):
        """Test initialization with integer identifier."""
        error = NotFoundError("Model", 123)
        assert "Model with identifier '123' not found" in error.message
        assert error.details["identifier"] == "123"


class TestUnauthorizedError:
    """Test UnauthorizedError class."""

    def test_init_default(self):
        """Test initialization with default message."""
        error = UnauthorizedError()
        assert error.message == "Authentication required"
        assert error.error_code == ErrorCode.UNAUTHORIZED

    def test_init_custom_message(self):
        """Test initialization with custom message."""
        error = UnauthorizedError("Invalid token")
        assert error.message == "Invalid token"


class TestDatabaseConnectionError:
    """Test DatabaseConnectionError class."""

    def test_init_basic(self):
        """Test basic initialization."""
        error = DatabaseConnectionError("Connection failed")
        assert error.message == "Connection failed"
        assert error.error_code == ErrorCode.DATABASE_CONNECTION_ERROR


class TestModelNotFoundError:
    """Test ModelNotFoundError class."""

    def test_init_with_name_only(self):
        """Test initialization with model name only."""
        error = ModelNotFoundError("test_model")
        assert "Model 'test_model' not found" in error.message
        assert error.details["model_name"] == "test_model"

    def test_init_with_version(self):
        """Test initialization with model name and version."""
        error = ModelNotFoundError("test_model", "v1.0")
        assert "Model 'test_model' version 'v1.0' not found" in error.message
        assert error.details["model_name"] == "test_model"
        assert error.details["version"] == "v1.0"


class TestPredictionError:
    """Test PredictionError class."""

    def test_init_default(self):
        """Test initialization with default message."""
        error = PredictionError()
        assert error.message == "Prediction failed"
        assert error.error_code == ErrorCode.PREDICTION_ERROR

    def test_init_custom(self):
        """Test initialization with custom parameters."""
        error = PredictionError("Custom error", model_name="test_model")
        assert error.message == "Custom error"


class TestExceptionBehavior:
    """Test exception behavior."""

    def test_exception_raising(self):
        """Test exceptions can be raised and caught."""
        with pytest.raises(BaseApplicationError):
            raise BaseApplicationError("Test", ErrorCode.INTERNAL_SERVER_ERROR)

        with pytest.raises(ValidationError):
            raise ValidationError("Test validation")

        with pytest.raises(NotFoundError):
            raise NotFoundError("Resource", "id")

    def test_inheritance_chain(self):
        """Test inheritance works correctly."""
        validation_error = ValidationError("Test")
        assert isinstance(validation_error, BaseApplicationError)
        assert isinstance(validation_error, Exception)

        not_found_error = NotFoundError("Test", "id")
        assert isinstance(not_found_error, BaseApplicationError)
        assert isinstance(not_found_error, Exception)

    def test_details_handling(self):
        """Test details are handled correctly."""
        error = BaseApplicationError(
            "Test",
            ErrorCode.VALIDATION_ERROR,
            details={"field": "username", "value": None},
        )
        assert error.details["field"] == "username"
        assert error.details["value"] is None

    def test_error_serialization(self):
        """Test errors serialize correctly."""
        error = ValidationError("Test error", field="email")
        serialized = error.to_dict()

        assert serialized["type"] == "ValidationError"
        assert serialized["error_code"] == "VALIDATION_ERROR"
        assert serialized["message"] == "Test error"
        assert serialized["details"]["field"] == "email"

    def test_multiple_error_codes(self):
        """Test multiple error codes work correctly."""
        codes = [
            ErrorCode.VALIDATION_ERROR,
            ErrorCode.NOT_FOUND,
            ErrorCode.UNAUTHORIZED,
            ErrorCode.MODEL_NOT_FOUND,
            ErrorCode.DATABASE_CONNECTION_ERROR,
            ErrorCode.PREDICTION_ERROR,
        ]

        for code in codes:
            assert isinstance(code, str)
            assert len(code.value) > 0
