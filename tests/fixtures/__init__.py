"""
测试夹具包

提供各种测试所需的夹具和工厂函数。
"""

from .api_fixtures import async_client, authenticated_client, mock_app
from .cache_fixtures import clean_cache, redis_client
from .database_fixtures import async_db_session, clean_database
from .factories import MatchFactory, PredictionFactory, TeamFactory, UserFactory

__all__ = [
    # Factories
    "MatchFactory",
    "PredictionFactory",
    "TeamFactory",
    "UserFactory",
    # API fixtures
    "async_client",
    # Database fixtures
    "async_db_session",
    "authenticated_client",
    "clean_cache",
    "clean_database",
    "mock_app",
    # Cache fixtures
    "redis_client",
]
