"""
测试 FootballAPICollector 的增强功能
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from httpx import Response

from data_pipeline.sources.football_api import FootballAPICollector, Team


class TestFootballAPICollectorEnhanced:
    """测试 FootballAPICollector 的增强功能"""

    @pytest.fixture
    def collector(self):
        """创建测试用的收集器实例"""
        return FootballAPICollector(api_key="test_key")

    @pytest.fixture
    def mock_session(self):
        """创建模拟的HTTP会话"""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_collect_team_info_success(self, collector, mock_session):
        """测试成功收集球队信息"""
        collector.session = mock_session

        # 模拟API响应
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "name": "Liverpool FC",
            "area": {"name": "England"},
            "founded": 1892,
            "venue": "Anfield",
        }
        mock_session.get.return_value = mock_response

        # 执行测试
        teams = await collector.collect_team_info(["123"])

        # 验证结果
        assert len(teams) == 1
        assert teams[0].team_id == "123"
        assert teams[0].name == "Liverpool FC"
        assert teams[0].league == "England"
        assert teams[0].founded == 1892
        assert teams[0].venue == "Anfield"

    @pytest.mark.asyncio
    async def test_collect_team_info_concurrent(self, collector, mock_session):
        """测试并发收集多个球队信息"""
        collector.session = mock_session

        # 模拟多个API响应
        def mock_response_factory(team_id):
            mock_response = Mock(spec=Response)
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = {
                "id": int(team_id),
                "name": f"Team {team_id}",
                "area": {"name": "Test League"},
                "founded": 1900 + int(team_id),
                "venue": f"Stadium {team_id}",
            }
            return mock_response

        async def mock_get(url, **kwargs):
            team_id = url.split("/")[-1]
            return mock_response_factory(team_id)

        mock_session.get.side_effect = mock_get

        # 执行测试
        teams = await collector.collect_team_info(["1", "2", "3"])

        # 验证结果
        assert len(teams) == 3
        assert all(isinstance(team, Team) for team in teams)
        assert all(team.league == "Test League" for team in teams)

    @pytest.mark.asyncio
    async def test_collect_team_info_with_api_error(self, collector, mock_session):
        """测试API错误时的降级处理"""
        collector.session = mock_session

        # 模拟API错误
        mock_session.get.side_effect = Exception("API Error")

        # 执行测试
        teams = await collector.collect_team_info(["123", "456"])

        # 验证降级结果
        assert len(teams) == 2
        assert teams[0].team_id == "123"
        assert teams[0].name == "Team_123"
        assert teams[0].league == "Unknown"
        assert teams[1].team_id == "456"
        assert teams[1].name == "Team_456"

    @pytest.mark.asyncio
    async def test_collect_team_info_partial_failure(self, collector, mock_session):
        """测试部分成功，部分失败的情况"""
        collector.session = mock_session

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # 第一个请求成功
                mock_response = Mock(spec=Response)
                mock_response.raise_for_status = Mock()
                mock_response.json.return_value = {
                    "id": 123,
                    "name": "Real Madrid",
                    "area": {"name": "Spain"},
                    "founded": 1902,
                    "venue": "Santiago Bernabéu",
                }
                return mock_response
            else:
                # 第二个请求失败
                raise Exception("API Error")

        mock_session.get.side_effect = mock_get

        # 执行测试
        teams = await collector.collect_team_info(["123", "456"])

        # 验证结果
        assert len(teams) == 2
        # 第一个成功的请求
        assert teams[0].name == "Real Madrid"
        assert teams[0].league == "Spain"
        # 第二个失败的请求使用降级数据
        assert teams[1].name == "Team_456"
        assert teams[1].league == "Unknown"

    @pytest.mark.asyncio
    async def test_collect_team_info_concurrency_limit(self, collector, mock_session):
        """测试并发限制功能"""
        collector.session = mock_session

        # 记录并发调用
        concurrent_calls = []
        max_concurrent = 0
        current_concurrent = 0

        async def mock_get(url, **kwargs):
            nonlocal current_concurrent, max_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            concurrent_calls.append(current_concurrent)

            # 模拟API延迟
            await asyncio.sleep(0.01)

            current_concurrent -= 1

            mock_response = Mock(spec=Response)
            mock_response.raise_for_status = Mock()
            mock_response.json.return_value = {
                "id": 123,
                "name": "Test Team",
                "area": {"name": "Test"},
            }
            return mock_response

        mock_session.get.side_effect = mock_get

        # 执行测试（10个并发请求）
        team_ids = [str(i) for i in range(10)]
        teams = await collector.collect_team_info(team_ids)

        # 验证结果
        assert len(teams) == 10
        # 验证并发数量被限制在5个以内
        assert max_concurrent <= 5

    @pytest.mark.asyncio
    async def test_collect_team_info_no_session(self, collector):
        """测试没有会话时抛出错误"""
        collector.session = None

        with pytest.raises(RuntimeError, match="需要在async with语句中使用"):
            await collector.collect_team_info(["123"])

    @pytest.mark.asyncio
    async def test_collect_team_info_empty_list(self, collector, mock_session):
        """测试空的球队ID列表"""
        collector.session = mock_session

        teams = await collector.collect_team_info([])

        assert teams == []
        mock_session.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_collect_team_info_missing_fields(self, collector, mock_session):
        """测试API响应缺少字段的情况"""
        collector.session = mock_session

        # 模拟不完整的API响应
        mock_response = Mock(spec=Response)
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "id": 123,
            "name": "Minimal Team",
            # 缺少其他字段
        }
        mock_session.get.return_value = mock_response

        teams = await collector.collect_team_info(["123"])

        assert len(teams) == 1
        assert teams[0].team_id == "123"
        assert teams[0].name == "Minimal Team"
        assert teams[0].league == "Unknown"  # 默认值
        assert teams[0].founded is None
        assert teams[0].venue is None
