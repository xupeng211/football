"""
数据库测试夹具

提供异步数据库会话、测试数据等数据库测试所需的夹具。
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """异步数据库会话"""
    # 模拟异步数据库会话
    mock_session = AsyncMock(spec=AsyncSession)

    # 配置常用方法
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.scalar = AsyncMock()

    yield mock_session

    # 清理
    await mock_session.rollback()
    await mock_session.close()


@pytest.fixture
def clean_database():
    """清理数据库"""
    # 在测试前后清理数据库
    yield
    # 这里可以添加实际的数据库清理逻辑


@pytest.fixture
def sample_data():
    """提供测试用的样本数据"""
    return {
        "teams": [
            {
                "id": "team_1",
                "name": "Manchester United",
                "league": "Premier League",
                "country": "England",
            },
            {
                "id": "team_2",
                "name": "Liverpool",
                "league": "Premier League",
                "country": "England",
            },
        ],
        "matches": [
            {
                "id": "match_1",
                "home_team_id": "team_1",
                "away_team_id": "team_2",
                "date": "2024-01-15T15:00:00",
                "status": "scheduled",
            }
        ],
        "predictions": [
            {
                "id": "pred_1",
                "match_id": "match_1",
                "home_win_prob": 0.45,
                "draw_prob": 0.30,
                "away_win_prob": 0.25,
                "confidence": 0.85,
            }
        ],
    }


@pytest_asyncio.fixture
async def mock_database_manager():
    """模拟数据库管理器"""
    with patch(
        "src.football_predict_system.core.database.get_database_manager"
    ) as mock_manager:
        manager_instance = MagicMock()

        # 模拟异步会话
        mock_session = AsyncMock(spec=AsyncSession)
        manager_instance.get_async_session = AsyncMock(return_value=mock_session)

        # 模拟健康检查
        manager_instance.health_check = AsyncMock(
            return_value={"status": "healthy", "latency": 0.01}
        )

        # 模拟关闭
        manager_instance.close = AsyncMock()

        mock_manager.return_value = manager_instance
        yield manager_instance
