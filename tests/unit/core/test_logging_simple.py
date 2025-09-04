"""
Simplified tests for core logging system.

Tests the actual available components to achieve coverage improvement.
"""

import time
from unittest.mock import Mock
from uuid import uuid4

import pytest

from football_predict_system.core.logging import (
    CorrelationIDProcessor,
    ErrorProcessor,
    PerformanceProcessor,
    clear_context,
    correlation_id_var,
    get_logger,
    request_id_var,
    set_correlation_id,
    set_request_id,
    set_user_id,
    user_id_var,
)


class TestCorrelationIDProcessor:
    """Test CorrelationIDProcessor functionality."""

    def setup_method(self):
        """Clean context before each test."""
        clear_context()

    def test_processor_with_correlation_id(self):
        """Test processor adds correlation ID when available."""
        processor = CorrelationIDProcessor()
        correlation_id = str(uuid4())

        # Set correlation ID in context
        set_correlation_id(correlation_id)

        # Process event dict
        event_dict = {"message": "test"}
        result = processor(Mock(), "info", event_dict)

        assert result["correlation_id"] == correlation_id
        assert result["message"] == "test"

    def test_processor_with_user_id(self):
        """Test processor adds user ID when available."""
        processor = CorrelationIDProcessor()
        user_id = "test-user-123"

        # Set user ID in context
        set_user_id(user_id)

        # Process event dict
        event_dict = {"message": "test"}
        result = processor(Mock(), "info", event_dict)

        assert result["user_id"] == user_id
        assert "correlation_id" not in result

    def test_processor_with_request_id(self):
        """Test processor adds request ID when available."""
        processor = CorrelationIDProcessor()
        request_id = str(uuid4())

        # Set request ID in context
        set_request_id(request_id)

        # Process event dict
        event_dict = {"message": "test"}
        result = processor(Mock(), "info", event_dict)

        assert result["request_id"] == request_id

    def test_processor_with_no_context(self):
        """Test processor when no context variables are set."""
        processor = CorrelationIDProcessor()

        # Process event dict without context
        event_dict = {"message": "test"}
        result = processor(Mock(), "info", event_dict)

        # Should only contain original message
        assert result == {"message": "test"}


class TestPerformanceProcessor:
    """Test PerformanceProcessor functionality."""

    def test_processor_adds_timestamp(self):
        """Test processor adds timestamp to events."""
        processor = PerformanceProcessor()

        start_time = time.time()
        event_dict = {"message": "test"}
        result = processor(Mock(), "info", event_dict)
        end_time = time.time()

        assert "timestamp" in result
        assert start_time <= result["timestamp"] <= end_time
        assert result["message"] == "test"

    def test_processor_with_duration_fast(self):
        """Test processor with fast duration (< 1s)."""
        processor = PerformanceProcessor()

        event_dict = {"message": "test", "duration": 0.5}
        result = processor(Mock(), "info", event_dict)

        assert "performance" in result
        assert result["performance"]["duration_ms"] == 500.0
        assert result["performance"]["slow_query"] is False

    def test_processor_with_duration_slow(self):
        """Test processor with slow duration (> 1s)."""
        processor = PerformanceProcessor()

        event_dict = {"message": "test", "duration": 2.5}
        result = processor(Mock(), "info", event_dict)

        assert "performance" in result
        assert result["performance"]["duration_ms"] == 2500.0
        assert result["performance"]["slow_query"] is True

    def test_processor_without_duration(self):
        """Test processor when no duration is provided."""
        processor = PerformanceProcessor()

        event_dict = {"message": "test"}
        result = processor(Mock(), "info", event_dict)

        assert "timestamp" in result
        assert "performance" not in result
        assert result["message"] == "test"


class TestErrorProcessor:
    """Test ErrorProcessor functionality."""

    def test_processor_with_error_method(self):
        """Test processor processes error level messages."""
        processor = ErrorProcessor()

        event_dict = {"message": "An error occurred"}
        result = processor(Mock(), "error", event_dict)

        # Should add stack trace for error level
        assert "stack_trace" in result
        assert result["message"] == "An error occurred"

    def test_processor_with_exception_object(self):
        """Test processor handles exception objects."""
        processor = ErrorProcessor()

        error = ValueError("Test error message")
        event_dict = {"message": "Error occurred", "error": error}
        result = processor(Mock(), "error", event_dict)

        # Should process the exception
        assert "error_details" in result
        assert result["error_details"]["type"] == "ValueError"
        assert result["error_details"]["message"] == "Test error message"
        assert "traceback" in result["error_details"]
        assert result["error"] == "Test error message"

    def test_processor_with_info_level(self):
        """Test processor doesn't add error details for info level."""
        processor = ErrorProcessor()

        event_dict = {"message": "Info message"}
        result = processor(Mock(), "info", event_dict)

        # Should not add error details for non-error levels
        assert "error_details" not in result
        assert "stack_trace" not in result
        assert result["message"] == "Info message"

    def test_processor_with_string_error(self):
        """Test processor handles string errors."""
        processor = ErrorProcessor()

        event_dict = {"message": "Error occurred", "error": "String error"}
        result = processor(Mock(), "error", event_dict)

        # Should add stack trace but not error_details for string errors
        assert "stack_trace" in result
        assert "error_details" not in result
        assert result["error"] == "String error"


class TestContextManagement:
    """Test context variable management functions."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def test_set_correlation_id_with_value(self):
        """Test setting correlation ID with specific value."""
        correlation_id = str(uuid4())

        result = set_correlation_id(correlation_id)
        assert result == correlation_id
        assert correlation_id_var.get() == correlation_id

    def test_set_correlation_id_generates_uuid(self):
        """Test setting correlation ID generates UUID when None."""
        result = set_correlation_id(None)

        # Should generate a UUID
        assert result is not None
        assert len(result) == 36  # UUID string length
        assert correlation_id_var.get() == result

    def test_set_user_id(self):
        """Test setting user ID."""
        user_id = "test-user-123"

        set_user_id(user_id)
        assert user_id_var.get() == user_id

    def test_set_request_id_with_value(self):
        """Test setting request ID with specific value."""
        request_id = str(uuid4())

        result = set_request_id(request_id)
        assert result == request_id
        assert request_id_var.get() == request_id

    def test_set_request_id_generates_uuid(self):
        """Test setting request ID generates UUID when None."""
        result = set_request_id(None)

        # Should generate a UUID
        assert result is not None
        assert len(result) == 36  # UUID string length
        assert request_id_var.get() == result

    def test_clear_context(self):
        """Test clearing all context variables."""
        # Set all context variables
        set_correlation_id("corr-123")
        set_user_id("user-123")
        set_request_id("req-123")

        # Verify they're set
        assert correlation_id_var.get() == "corr-123"
        assert user_id_var.get() == "user-123"
        assert request_id_var.get() == "req-123"

        # Clear context
        clear_context()

        # Verify they're cleared
        assert correlation_id_var.get() is None
        assert user_id_var.get() is None
        assert request_id_var.get() is None


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a structlog logger."""
        logger = get_logger("test.module")

        # Should be a bound logger with standard methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")

    def test_get_logger_with_different_names(self):
        """Test get_logger with different module names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # Should return different logger instances
        assert logger1 is not logger2

    def test_get_logger_with_none_name(self):
        """Test get_logger with None name."""
        logger = get_logger(None)

        # Should return a logger instance
        assert logger is not None
        assert hasattr(logger, "info")


class TestLogPerformance:
    """Test log_performance decorator."""

    def test_decorator_basic_functionality(self):
        """Test basic decorator functionality."""
        # Import the decorator - check if it exists first
        try:
            from football_predict_system.core.logging import log_performance

            @log_performance("test_operation")
            def test_function():
                return "result"

            # Should preserve function behavior
            result = test_function()
            assert result == "result"

        except ImportError:
            # Skip if decorator doesn't exist
            pytest.skip("log_performance decorator not available")

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves function metadata."""
        try:
            from football_predict_system.core.logging import log_performance

            @log_performance("test_op")
            def documented_function():
                """Test function with docstring."""
                pass

            assert documented_function.__name__ == "documented_function"
            assert "Test function with docstring." in documented_function.__doc__

        except ImportError:
            pytest.skip("log_performance decorator not available")


class TestProcessorIntegration:
    """Integration tests for processors working together."""

    def setup_method(self):
        """Set up test environment."""
        clear_context()

    def test_multiple_processors_pipeline(self):
        """Test multiple processors working in sequence."""
        # Set up context
        correlation_id = str(uuid4())
        user_id = "test-user"
        set_correlation_id(correlation_id)
        set_user_id(user_id)

        # Create processors
        correlation_processor = CorrelationIDProcessor()
        performance_processor = PerformanceProcessor()
        error_processor = ErrorProcessor()

        # Test event processing
        event_dict = {"message": "User action", "duration": 1.5}

        # Process through pipeline
        result = correlation_processor(Mock(), "info", event_dict)
        result = performance_processor(Mock(), "info", result)
        result = error_processor(Mock(), "info", result)

        # Verify all processors worked
        assert result["correlation_id"] == correlation_id
        assert result["user_id"] == user_id
        assert "timestamp" in result
        assert result["performance"]["slow_query"] is True
        assert result["message"] == "User action"

    def test_error_processor_with_context(self):
        """Test error processor with context variables."""
        # Set context
        set_correlation_id("error-context")
        set_user_id("error-user")

        # Create processors
        correlation_processor = CorrelationIDProcessor()
        error_processor = ErrorProcessor()

        # Process error event
        error = RuntimeError("Test runtime error")
        event_dict = {"message": "Critical error", "error": error}

        # Process through pipeline
        result = correlation_processor(Mock(), "error", event_dict)
        result = error_processor(Mock(), "error", result)

        # Verify context and error processing
        assert result["correlation_id"] == "error-context"
        assert result["user_id"] == "error-user"
        assert "error_details" in result
        assert result["error_details"]["type"] == "RuntimeError"
        assert "stack_trace" in result


class TestContextVariables:
    """Test context variables directly."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def test_context_var_isolation(self):
        """Test that context variables work independently."""
        # Set only correlation ID
        set_correlation_id("test-correlation")

        assert correlation_id_var.get() == "test-correlation"
        assert user_id_var.get() is None
        assert request_id_var.get() is None

        # Set only user ID
        clear_context()
        set_user_id("test-user")

        assert correlation_id_var.get() is None
        assert user_id_var.get() == "test-user"
        assert request_id_var.get() is None

    def test_context_var_overwrite(self):
        """Test that context variables can be overwritten."""
        # Set initial values
        set_correlation_id("first-correlation")
        set_user_id("first-user")

        assert correlation_id_var.get() == "first-correlation"
        assert user_id_var.get() == "first-user"

        # Overwrite values
        set_correlation_id("second-correlation")
        set_user_id("second-user")

        assert correlation_id_var.get() == "second-correlation"
        assert user_id_var.get() == "second-user"

    def test_uuid_generation_uniqueness(self):
        """Test that generated UUIDs are unique."""
        uuid1 = set_correlation_id(None)
        uuid2 = set_correlation_id(None)
        uuid3 = set_request_id(None)
        uuid4 = set_request_id(None)

        # All should be different
        uuids = [uuid1, uuid2, uuid3, uuid4]
        assert len(set(uuids)) == 4  # All unique
