"""
API main module - Re-exports the main FastAPI application instance.

This module provides compatibility for tests and scripts that expect
to import the app from football_predict_system.api.main.
"""

from football_predict_system.main import app

__all__ = ["app"]
