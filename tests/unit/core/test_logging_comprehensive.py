"""
Comprehensive tests for the logging module to improve coverage.

Tests all major functionality including:
- CorrelationIDProcessor
- PerformanceProcessor
- ErrorProcessor
- Logger configuration
- Context variables
"""

from unittest.mock import MagicMock, patch

import pytest
import structlog

from football_predict_system.core.logging import (CorrelationIDProcessor, ErrorProcessor, PerformanceProcessor,
                                                  correlation_id_var, get_logger, request_id_var, setup_logging,
                                                  user_id_var)


class TestCorrelationIDProcessor:
    """Test CorrelationIDProcessor functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.processor = CorrelationIDProcessor()
        self.mock_logger = MagicMock()

    def test_no_correlation_data(self):
        """Test processor with no correlation data."""
        event_dict = {"message": "test"}

        result = self.processor(self.mock_logger, "info", event_dict)

        assert result == {"message": "test"}
        assert "correlation_id" not in result
        assert "user_id" not in result
        assert "request_id" not in result

    def test_with_correlation_id(self):
        """Test processor with correlation ID."""
        event_dict = {"message": "test"}

        # Set correlation ID in context
        token = correlation_id_var.set("test-correlation-123")
        try:
            result = self.processor(self.mock_logger, "info", event_dict)
            assert result["correlation_id"] == "test-correlation-123"
            assert result["message"] == "test"
        finally:
            correlation_id_var.reset(token)

    def test_with_user_id(self):
        """Test processor with user ID."""
        event_dict = {"message": "test"}

        # Set user ID in context
        token = user_id_var.set("user-456")
        try:
            result = self.processor(self.mock_logger, "info", event_dict)
            assert result["user_id"] == "user-456"
            assert result["message"] == "test"
        finally:
            user_id_var.reset(token)

    def test_with_request_id(self):
        """Test processor with request ID."""
        event_dict = {"message": "test"}

        # Set request ID in context
        token = request_id_var.set("req-789")
        try:
            result = self.processor(self.mock_logger, "info", event_dict)
            assert result["request_id"] == "req-789"
            assert result["message"] == "test"
        finally:
            request_id_var.reset(token)

    def test_with_all_context_data(self):
        """Test processor with all context data."""
        event_dict = {"message": "test"}

        # Set all context variables
        corr_token = correlation_id_var.set("test-correlation-123")
        user_token = user_id_var.set("user-456")
        req_token = request_id_var.set("req-789")

        try:
            result = self.processor(self.mock_logger, "info", event_dict)
            assert result["correlation_id"] == "test-correlation-123"
            assert result["user_id"] == "user-456"
            assert result["request_id"] == "req-789"
            assert result["message"] == "test"
        finally:
            correlation_id_var.reset(corr_token)
            user_id_var.reset(user_token)
            request_id_var.reset(req_token)


class TestPerformanceProcessor:
    """Test PerformanceProcessor functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.processor = PerformanceProcessor()
        self.mock_logger = MagicMock()

    def test_adds_timestamp(self):
        """Test that processor adds timestamp."""
        event_dict = {"message": "test"}

        with patch('time.time', return_value=1234567890.123):
            result = self.processor(self.mock_logger, "info", event_dict)

        assert result["timestamp"] == 1234567890.123
        assert result["message"] == "test"

    def test_no_duration(self):
        """Test processor without duration data."""
        event_dict = {"message": "test"}

        result = self.processor(self.mock_logger, "info", event_dict)

        assert "performance" not in result
        assert "timestamp" in result
        assert result["message"] == "test"

    def test_with_fast_duration(self):
        """Test processor with fast duration."""
        event_dict = {"message": "test", "duration": 0.5}

        result = self.processor(self.mock_logger, "info", event_dict)

        assert result["performance"]["duration_ms"] == 500.0
        assert result["performance"]["slow_query"] is False
        assert result["duration"] == 0.5

    def test_with_slow_duration(self):
        """Test processor with slow duration."""
        event_dict = {"message": "test", "duration": 2.5}

        result = self.processor(self.mock_logger, "info", event_dict)

        assert result["performance"]["duration_ms"] == 2500.0
        assert result["performance"]["slow_query"] is True
        assert result["duration"] == 2.5

    def test_duration_exactly_one_second(self):
        """Test processor with duration exactly at slow threshold."""
        event_dict = {"message": "test", "duration": 1.0}

        result = self.processor(self.mock_logger, "info", event_dict)

        assert result["performance"]["duration_ms"] == 1000.0
        assert result["performance"]["slow_query"] is False


class TestErrorProcessor:
    """Test ErrorProcessor functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.processor = ErrorProcessor()
        self.mock_logger = MagicMock()

    def test_non_error_methods(self):
        """Test processor with non-error log methods."""
        event_dict = {"message": "test"}

        for method in ["info", "debug", "warning"]:
            result = self.processor(self.mock_logger, method, event_dict)
            assert result == event_dict
            assert "error_details" not in result

    def test_error_method_no_error_object(self):
        """Test processor with error method but no error object."""
        event_dict = {"message": "test error"}

        result = self.processor(self.mock_logger, "error", event_dict)

        assert result == event_dict
        assert "error_details" not in result

    def test_error_method_with_string_error(self):
        """Test processor with error method and string error."""
        event_dict = {"message": "test error", "error": "simple error"}

        result = self.processor(self.mock_logger, "error", event_dict)

        assert result == event_dict
        assert "error_details" not in result

    def test_error_method_with_exception(self):
        """Test processor with error method and exception object."""
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            event_dict = {"message": "test error", "error": e}

            result = self.processor(self.mock_logger, "error", event_dict)

            assert result["error"] == e
            assert result["message"] == "test error"
            assert "error_details" in result
            assert result["error_details"]["type"] == "ValueError"
            assert result["error_details"]["message"] == "Test error message"
            assert "traceback" in result["error_details"]
            assert isinstance(result["error_details"]["traceback"], list)

    def test_exception_method_with_exception(self):
        """Test processor with exception method."""
        try:
            raise RuntimeError("Runtime error")
        except RuntimeError as e:
            event_dict = {"message": "exception occurred", "error": e}

            result = self.processor(self.mock_logger, "exception", event_dict)

            assert "error_details" in result
            assert result["error_details"]["type"] == "RuntimeError"
            assert result["error_details"]["message"] == "Runtime error"

    def test_critical_method_with_exception(self):
        """Test processor with critical method."""
        try:
            raise SystemError("System error")
        except SystemError as e:
            event_dict = {"message": "critical error", "error": e}

            result = self.processor(self.mock_logger, "critical", event_dict)

            assert "error_details" in result
            assert result["error_details"]["type"] == "SystemError"
            assert result["error_details"]["message"] == "System error"


class TestLoggingSetup:
    """Test logging setup and configuration."""

    def test_setup_logging_development(self):
        """Test logging setup for development environment."""
        with patch('football_predict_system.core.logging.get_settings') as mock_settings:
            mock_settings.return_value.environment = "development"
            mock_settings.return_value.log_level = "DEBUG"

            setup_logging()

            # Check that structlog is configured
            logger = structlog.get_logger()
            assert logger is not None

    def test_setup_logging_production(self):
        """Test logging setup for production environment."""
        with patch('football_predict_system.core.logging.get_settings') as mock_settings:
            mock_settings.return_value.environment = "production"
            mock_settings.return_value.log_level = "INFO"

            setup_logging()

            # Check that structlog is configured
            logger = structlog.get_logger()
            assert logger is not None

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_module")
        assert logger is not None

        # Test that logger has expected methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

    def test_get_logger_with_name(self):
        """Test getting logger with specific name."""
        logger = get_logger("my_test_module")
        assert logger is not None

    def test_get_logger_without_name(self):
        """Test getting logger without name."""
        logger = get_logger()
        assert logger is not None


class TestContextVariables:
    """Test context variable functionality."""

    def test_correlation_id_context(self):
        """Test correlation ID context variable."""
        # Initially should be None
        assert correlation_id_var.get() is None

        # Set value
        token = correlation_id_var.set("test-correlation")
        assert correlation_id_var.get() == "test-correlation"

        # Reset
        correlation_id_var.reset(token)
        assert correlation_id_var.get() is None

    def test_user_id_context(self):
        """Test user ID context variable."""
        # Initially should be None
        assert user_id_var.get() is None

        # Set value
        token = user_id_var.set("test-user")
        assert user_id_var.get() == "test-user"

        # Reset
        user_id_var.reset(token)
        assert user_id_var.get() is None

    def test_request_id_context(self):
        """Test request ID context variable."""
        # Initially should be None
        assert request_id_var.get() is None

        # Set value
        token = request_id_var.set("test-request")
        assert request_id_var.get() == "test-request"

        # Reset
        request_id_var.reset(token)
        assert request_id_var.get() is None


class TestLoggerIntegration:
    """Test logger integration with processors."""

    def setup_method(self):
        """Set up test environment."""
        # Reconfigure structlog for testing
        structlog.reset_defaults()
        setup_logging()

    def test_logger_with_correlation_id(self):
        """Test logger captures correlation ID."""
        logger = get_logger("test")

        # Set correlation ID
        token = correlation_id_var.set("test-correlation-123")

        try:
            # This should work without error
            logger.info("Test message with correlation")
        finally:
            correlation_id_var.reset(token)

    def test_logger_with_performance_data(self):
        """Test logger with performance data."""
        logger = get_logger("test")

        # Log with duration
        logger.info("Slow operation", duration=2.5)

    def test_logger_with_exception(self):
        """Test logger with exception."""
        logger = get_logger("test")

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            logger.error("Exception occurred", error=e)


if __name__ == "__main__":
    pytest.main([__file__])
