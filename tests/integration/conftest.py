"""
Integration Test Configuration and Fixtures

This module provides shared fixtures and configuration for integration tests
that test the interaction between multiple components of the football prediction system.
"""

import asyncio
import os
import shutil
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Set testing environment
os.environ["ENV"] = "testing"
os.environ["TESTING"] = "true"
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")

from football_predict_system.core.database import get_database_manager
from football_predict_system.core.health import get_health_checker
from football_predict_system.main import app


class IntegrationTestConfig:
    """Configuration for integration tests."""

    def __init__(self):
        self.base_url = "http://testserver"
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.temp_dir = None

        # Test database configuration
        self.test_db_url = "sqlite:///:memory:"

        # Test Redis configuration (mock)
        self.test_redis_url = "redis://localhost:6379/15"  # Use test DB

        # API endpoints to test
        self.api_endpoints = {
            "health": "/health",
            "health_ready": "/health/ready",
            "health_live": "/health/live",
            "metrics": "/metrics",
            "api_v1": "/api/v1",
            "predictions": "/api/v1/predictions",
            "models": "/api/v1/models"
        }

    def setup_temp_directory(self) -> Path:
        """Create temporary directory for test files."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="football_test_"))
        return self.temp_dir

    def cleanup_temp_directory(self):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def integration_config():
    """Provide integration test configuration."""
    config = IntegrationTestConfig()
    config.setup_temp_directory()
    yield config
    config.cleanup_temp_directory()


@pytest_asyncio.fixture(scope="session")
async def test_app():
    """Create test FastAPI application with mocked dependencies."""

    # Mock settings for testing
    with patch("football_predict_system.core.config.get_settings") as mock_settings:
        mock_settings.return_value.database_url = "sqlite:///:memory:"
        mock_settings.return_value.redis_url = "redis://localhost:6379/15"
        mock_settings.return_value.debug = True
        mock_settings.return_value.testing = True

        yield app


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    async with AsyncClient(app=test_app, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def database_manager():
    """Provide database manager for integration tests."""
    # Use in-memory SQLite for fast testing
    with patch("football_predict_system.core.config.get_settings") as mock_settings:
        mock_settings.return_value.database_url = "sqlite:///:memory:"

        db_manager = get_database_manager()
        await db_manager.initialize()

        try:
            yield db_manager
        finally:
            await db_manager.close()


@pytest_asyncio.fixture
async def cache_manager():
    """Provide cache manager for integration tests."""
    # Use mock cache for testing
    from unittest.mock import AsyncMock, MagicMock

    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock(return_value=True)
    mock_cache.delete = AsyncMock(return_value=True)
    mock_cache.clear = AsyncMock(return_value=True)
    mock_cache.exists = AsyncMock(return_value=False)
    mock_cache.ttl = AsyncMock(return_value=-1)
    mock_cache.stats = MagicMock(return_value={
        "hits": 0,
        "misses": 0,
        "total_requests": 0,
        "hit_rate": 0.0
    })

    with patch("football_predict_system.core.cache.get_cache_manager") as mock_get_cache:
        mock_get_cache.return_value = mock_cache
        yield mock_cache


@pytest_asyncio.fixture
async def health_checker(database_manager, cache_manager):
    """Provide health checker for integration tests."""
    health_checker = get_health_checker()
    yield health_checker


@pytest.fixture
def sample_match_data():
    """Provide sample match data for testing."""
    return {
        "home_team": "Manchester United",
        "away_team": "Liverpool",
        "date": "2024-01-15T15:00:00Z",
        "league": "Premier League",
        "season": "2023-24"
    }


@pytest.fixture
def sample_prediction_request():
    """Provide sample prediction request data."""
    return {
        "match": {
            "home_team": "Manchester United",
            "away_team": "Liverpool",
            "date": "2024-01-15T15:00:00Z",
            "league": "Premier League"
        },
        "features": {
            "home_form": [1, 1, 0, 1, 1],  # Last 5 matches
            "away_form": [1, 0, 1, 1, 0],
            "head_to_head": [0, 1, 0],     # Last 3 H2H
            "league_position_home": 3,
            "league_position_away": 1
        },
        "options": {
            "include_confidence": True,
            "detailed_analysis": True
        }
    }


@pytest.fixture
def sample_batch_prediction_request():
    """Provide sample batch prediction request data."""
    return {
        "matches": [
            {
                "home_team": "Manchester United",
                "away_team": "Liverpool",
                "date": "2024-01-15T15:00:00Z",
                "league": "Premier League"
            },
            {
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "date": "2024-01-15T17:30:00Z",
                "league": "Premier League"
            }
        ],
        "options": {
            "include_confidence": True,
            "parallel_processing": True
        }
    }


@pytest.fixture
def mock_model_response():
    """Provide mock model prediction response."""
    return {
        "prediction": {
            "home_win_probability": 0.45,
            "draw_probability": 0.25,
            "away_win_probability": 0.30,
            "predicted_result": "home_win",
            "confidence": 0.78
        },
        "analysis": {
            "key_factors": [
                "Home advantage",
                "Recent form favor home team",
                "Head-to-head record"
            ],
            "risk_factors": [
                "Away team has strong away record",
                "Key player injuries for home team"
            ]
        },
        "metadata": {
            "model_version": "v3.0.0",
            "prediction_timestamp": "2024-01-10T10:30:00Z",
            "features_used": 15
        }
    }


@pytest.fixture
def api_headers():
    """Provide standard API headers for testing."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "FootballPredictIntegrationTest/1.0"
    }


class DatabaseTestHelper:
    """Helper class for database operations in tests."""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    async def create_test_match(self, match_data: dict[str, Any]):
        """Create a test match in the database."""
        # Implementation would depend on actual database schema
        pass

    async def create_test_team(self, team_data: dict[str, Any]):
        """Create a test team in the database."""
        pass

    async def cleanup_test_data(self):
        """Clean up test data from database."""
        pass


@pytest.fixture
async def db_helper(database_manager):
    """Provide database helper for tests."""
    helper = DatabaseTestHelper(database_manager)
    yield helper
    await helper.cleanup_test_data()


class CacheTestHelper:
    """Helper class for cache operations in tests."""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager

    async def populate_test_cache(self, test_data: dict[str, Any]):
        """Populate cache with test data."""
        for key, value in test_data.items():
            await self.cache_manager.set(key, value)

    async def verify_cache_state(self, expected_keys: list):
        """Verify cache contains expected keys."""
        for key in expected_keys:
            exists = await self.cache_manager.exists(key)
            assert exists, f"Cache key '{key}' should exist"

    async def clear_test_cache(self):
        """Clear all test cache data."""
        await self.cache_manager.clear()


@pytest.fixture
async def cache_helper(cache_manager):
    """Provide cache helper for tests."""
    helper = CacheTestHelper(cache_manager)
    yield helper
    await helper.clear_test_cache()


@pytest.fixture
def integration_test_scenarios():
    """Provide test scenarios for integration testing."""
    return {
        "api_health_flow": {
            "description": "Test complete API health check flow",
            "endpoints": ["/health", "/health/ready", "/health/live"],
            "expected_status": 200
        },
        "prediction_flow": {
            "description": "Test complete prediction flow",
            "steps": [
                "create_prediction_request",
                "validate_request",
                "process_prediction",
                "cache_result",
                "return_response"
            ]
        },
        "batch_prediction_flow": {
            "description": "Test batch prediction processing",
            "batch_sizes": [1, 5, 10, 25],
            "parallel_processing": True
        },
        "cache_integration": {
            "description": "Test cache integration with API",
            "cache_scenarios": [
                "cache_miss",
                "cache_hit",
                "cache_invalidation",
                "cache_expiry"
            ]
        },
        "database_integration": {
            "description": "Test database integration",
            "operations": [
                "read_teams",
                "read_matches",
                "store_predictions",
                "query_history"
            ]
        },
        "error_handling": {
            "description": "Test error handling across components",
            "error_types": [
                "database_connection_error",
                "cache_connection_error",
                "model_service_error",
                "invalid_request_data"
            ]
        }
    }


# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance tests."""
    return {
        "concurrent_requests": [1, 5, 10, 20],
        "request_duration": 30,  # seconds
        "acceptable_response_time": 2.0,  # seconds
        "acceptable_error_rate": 0.01,  # 1%
        "memory_threshold": "500MB",
        "cpu_threshold": 80  # percent
    }


@pytest.fixture
async def stress_test_data():
    """Generate data for stress testing."""
    import random
    teams = [
        "Manchester United", "Liverpool", "Arsenal", "Chelsea", "Manchester City",
        "Tottenham", "Newcastle", "Brighton", "West Ham", "Aston Villa"
    ]

    test_data = []
    for i in range(100):
        home_team = random.choice(teams)
        away_team = random.choice([t for t in teams if t != home_team])

        test_data.append({
            "home_team": home_team,
            "away_team": away_team,
            "date": f"2024-01-{(i % 30) + 1:02d}T15:00:00Z",
            "league": "Premier League"
        })

    return test_data
