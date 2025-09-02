import pytest

from football_predict_system.data_platform.sources.football_data_api import (
    FootballDataAPICollector,
)

pytestmark = pytest.mark.skip(reason="data_pipeline module not implemented")

"""
测试FootballAPICollector类的基本功能。

这是一个简化的测试模块, 专注于测试核心功能。
"""


def test_football_api_collector_creation():
    """测试FootballAPICollector的创建。"""
    collector = FootballDataAPICollector(api_key="test_key")
    assert collector is not None
    assert collector.api_key == "test_key"


def test_football_api_collector_default_api_key():
    """测试FootballAPICollector的默认API密钥行为。"""
    collector = FootballDataAPICollector()
    assert collector is not None
    # The default behavior should handle missing API key gracefully
