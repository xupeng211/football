"""
简化的足球API测试
"""

from data_pipeline.sources.football_api import FootballAPICollector


class TestFootballAPICollector:
    """足球API收集器测试"""

    def test_collector_initialization(self) -> None:
        """测试收集器初始化"""
        collector = FootballAPICollector()
        assert collector is not None
        assert hasattr(collector, "collect_matches_by_date")

    def test_collector_has_required_methods(self) -> None:
        """测试收集器有必需的方法"""
        collector = FootballAPICollector()
        assert hasattr(collector, "collect_matches_by_date")
        assert hasattr(collector, "collect_team_info")
        assert callable(collector.collect_matches_by_date)
        assert callable(collector.collect_team_info)
