"""
Unit tests for the logging configuration.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
import structlog

from apps.api.core.logging import (
    get_logger_with_trace,
    log_api_request,
    log_api_response,
    setup_logging,
)
from apps.api.core.settings import settings


@pytest.fixture(autouse=True)
def reset_structlog():
    """Fixture to reset structlog configuration before and after each test."""
    structlog.reset_defaults()
    yield
    structlog.reset_defaults()


class TestLoggingSetup:
    """Tests for the logging setup and configuration."""

    @patch("apps.api.core.logging.logging.basicConfig")
    def test_setup_logging_basic_config(self, mock_basic_config):
        """Tests that standard library logging is configured correctly."""
        with patch.object(settings, "log_level", "INFO"):
            setup_logging()
            mock_basic_config.assert_called_once()
            assert mock_basic_config.call_args[1]["level"] == logging.INFO

    @patch("apps.api.core.logging.structlog.configure")
    def test_setup_logging_json_format(self, mock_configure):
        """Tests that JSON renderer is used when log_format is 'json'."""
        with patch.object(settings, "log_format", "json"):
            setup_logging()
            mock_configure.assert_called_once()
            # Check that JSONRenderer is in the processor chain
            processors = mock_configure.call_args[1]["processors"]
            assert any(
                isinstance(p, structlog.processors.JSONRenderer) for p in processors
            )

    @patch("apps.api.core.logging.structlog.configure")
    def test_setup_logging_console_format(self, mock_configure):
        """Tests that ConsoleRenderer is used for non-json formats."""
        with patch.object(settings, "log_format", "console"):
            setup_logging()
            mock_configure.assert_called_once()
            # Check that ConsoleRenderer is in the processor chain
            processors = mock_configure.call_args[1]["processors"]
            assert any(isinstance(p, structlog.dev.ConsoleRenderer) for p in processors)


class TestLogHelpers:
    """Tests for logging helper functions."""

    def test_get_logger_with_trace(self):
        """Tests that a trace_id is correctly bound to the logger."""
        # We need to configure structlog for this test to work
        setup_logging()
        logger = get_logger_with_trace("test-trace-id")
        # The internal logger object has the context
        assert logger.bind.__self__._context == {"trace_id": "test-trace-id"}

    @patch("apps.api.core.logging.get_logger_with_trace")
    def test_log_api_request(self, mock_get_logger):
        """Tests the API request logging function."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        log_api_request("GET", "/test", "trace-123", extra="data")

        mock_get_logger.assert_called_once_with("trace-123")
        mock_logger.info.assert_called_once_with(
            "API请求", method="GET", path="/test", extra="data"
        )

    @patch("apps.api.core.logging.get_logger_with_trace")
    def test_log_api_response(self, mock_get_logger):
        """Tests the API response logging function."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        log_api_response("GET", "/test", 200, 55.5, "trace-123")

        mock_get_logger.assert_called_once_with("trace-123")
        mock_logger.info.assert_called_once_with(
            "API响应",
            method="GET",
            path="/test",
            status_code=200,
            duration_ms=55.5,
        )
