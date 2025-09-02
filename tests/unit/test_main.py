"""Tests for main application module."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI

from football_predict_system.main import app


class TestApp:
    """Test main FastAPI application."""

    def test_app_instance(self):
        """Test that app is a FastAPI instance."""
        assert isinstance(app, FastAPI)
        assert app.title == "Football Prediction System"

    def test_app_has_routers(self):
        """Test that app includes expected routers."""
        routes = [route.path for route in app.routes]

        # Should have some routes from included routers
        assert len(routes) > 0

    def test_app_middleware_configured(self):
        """Test that middleware is configured."""
        middleware_classes = [
            middleware.cls.__name__ for middleware in app.user_middleware
        ]

        # Should have CORS middleware
        assert any("CORS" in cls for cls in middleware_classes)

    def test_app_exception_handlers(self):
        """Test that exception handlers are configured."""
        # Check if exception handlers are registered
        assert hasattr(app, "exception_handlers")
        assert len(app.exception_handlers) > 0


class TestAppConfiguration:
    """Test application configuration."""

    @patch("football_predict_system.main.get_settings")
    def test_app_uses_settings(self, mock_get_settings):
        """Test that app uses settings configuration."""
        mock_settings = Mock()
        mock_settings.app_name = "Test App"
        mock_settings.debug = True
        mock_get_settings.return_value = mock_settings

        # Import main to trigger settings usage

        mock_get_settings.assert_called()

    def test_app_cors_configuration(self):
        """Test CORS configuration."""
        # Check if CORS is properly configured
        cors_middleware = None
        for middleware in app.user_middleware:
            if "CORS" in middleware.cls.__name__:
                cors_middleware = middleware
                break

        assert cors_middleware is not None


class TestLifespan:
    """Test application lifespan events."""

    @pytest.mark.asyncio
    @patch("football_predict_system.main.get_database_manager")
    @patch("football_predict_system.main.get_cache_manager")
    async def test_lifespan_startup(self, mock_get_cache_manager, mock_get_db_manager):
        """Test application startup sequence."""
        # Mock dependencies
        mock_db_manager = Mock()
        mock_db_manager.get_engine.return_value = Mock()
        mock_db_manager.get_async_engine.return_value = Mock()
        mock_db_manager.close = AsyncMock()

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_redis_client = AsyncMock(return_value=Mock())
        mock_cache_manager.close = AsyncMock()

        mock_get_db_manager.return_value = mock_db_manager
        mock_get_cache_manager.return_value = mock_cache_manager

        # Test lifespan context manager
        from football_predict_system.main import lifespan

        async with lifespan(app):
            # During startup, managers should be initialized
            mock_get_db_manager.assert_called_once()
            mock_get_cache_manager.assert_called_once()

        # During shutdown, managers should be closed
        mock_db_manager.close.assert_called_once()
        mock_cache_manager.close.assert_called_once()


class TestErrorHandling:
    """Test application error handling."""

    def test_base_application_error_handler_exists(self):
        """Test that BaseApplicationError handler exists."""
        from football_predict_system.core.exceptions import BaseApplicationError

        # Check if handler is registered
        assert BaseApplicationError in app.exception_handlers

    def test_error_handler_returns_json_response(self):
        """Test that error handler returns proper JSON response."""
        from unittest.mock import Mock

        from fastapi import Request

        from football_predict_system.core.exceptions import (
            BaseApplicationError,
            ErrorCode,
        )

        # Get the error handler
        handler = app.exception_handlers[BaseApplicationError]

        # Create a mock request and exception
        mock_request = Mock(spec=Request)
        mock_exception = BaseApplicationError(
            "Test error", error_code=ErrorCode.VALIDATION_ERROR
        )

        # Call the async handler
        import asyncio

        response = asyncio.run(handler(mock_request, mock_exception))

        # Should return a JSONResponse
        from fastapi.responses import JSONResponse

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400


class TestAppMetadata:
    """Test application metadata and configuration."""

    def test_app_version(self):
        """Test application version is set."""
        assert hasattr(app, "version")
        assert app.version is not None

    def test_app_description(self):
        """Test application description is set."""
        assert hasattr(app, "description")
        if app.description:
            assert isinstance(app.description, str)

    def test_app_docs_configuration(self):
        """Test API documentation configuration."""
        # Should have docs URL configured
        assert hasattr(app, "docs_url")
        assert hasattr(app, "redoc_url")

    def test_app_tags_metadata(self):
        """Test API tags metadata."""
        if hasattr(app, "openapi_tags"):
            assert isinstance(app.openapi_tags, list)
