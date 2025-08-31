"""
足球数据采集器 - 从外部API获取比赛数据
"""

import types
from dataclasses import dataclass
from datetime import date, datetime

import httpx
import structlog

from apps.api.core.settings import settings

logger = structlog.get_logger()


@dataclass
class Match:
    """比赛数据模型"""

    match_id: str
    home_team: str
    away_team: str
    league: str
    season: str
    match_date: datetime
    home_score: int | None = None
    away_score: int | None = None
    status: str = "scheduled"  # scheduled, live, finished
    venue: str | None = None


@dataclass
class Team:
    """球队数据模型"""

    team_id: str
    name: str
    league: str
    season: str
    founded: int | None = None
    venue: str | None = None


class FootballAPICollector:
    """足球数据采集器"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.football_api_key
        self.base_url = "https://api.football-data.org/v4"  # 示例API
        self.session: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "FootballAPICollector":
        """异步上下文管理器入口"""
        headers = {}
        if self.api_key:
            headers["X-Auth-Token"] = self.api_key

        self.session = httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """异步上下文管理器退出"""
        if self.session:
            await self.session.aclose()

    async def collect_matches_by_date(
        self,
        start_date: date,
        end_date: date,
        leagues: list[str] | None = None,
    ) -> list[Match]:
        """
        按日期范围收集比赛数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            leagues: 联赛列表, None表示所有联赛

        Returns:
            比赛数据列表
        """
        if not self.session:
            raise RuntimeError("需要在async with语句中使用")

        logger.info(
            "开始收集比赛数据",
            start_date=str(start_date),
            end_date=str(end_date),
            leagues=leagues,
        )

        matches = []

        try:
            params = {
                "dateFrom": start_date.strftime("%Y-%m-%d"),
                "dateTo": end_date.strftime("%Y-%m-%d"),
            }
            if leagues:
                params["competitions"] = ",".join(leagues)

            response = await self.session.get(f"{self.base_url}/matches", params=params)
            response.raise_for_status()
            data = response.json()

            for item in data.get("matches", []):
                matches.append(
                    Match(
                        match_id=str(item["id"]),
                        home_team=item["homeTeam"]["name"],
                        away_team=item["awayTeam"]["name"],
                        league=item["competition"]["code"],
                        season=str(item["season"]["currentMatchday"]),
                        match_date=datetime.fromisoformat(
                            item["utcDate"].replace("Z", "+00:00")
                        ),
                        home_score=item["score"]["fullTime"]["home"],
                        away_score=item["score"]["fullTime"]["away"],
                        status=item["status"].lower(),
                    )
                )

        except Exception as e:
            logger.error("Failed to collect match data", error=str(e))
            raise

        logger.info("Successfully collected match data", count=len(matches))
        return matches

    async def collect_team_info(self, team_ids: list[str]) -> list[Team]:
        """
        收集球队信息

        Args:
            team_ids: 球队ID列表

        Returns:
            球队信息列表
        """
        if not self.session:
            raise RuntimeError("需要在async with语句中使用")

        logger.info("开始收集球队信息", team_count=len(team_ids))

        teams = []

        try:
            # 实现并发API调用
            import asyncio

            async def fetch_team_info(team_id: str) -> Team:
                """获取单个球队信息"""
                try:
                    if not self.session:
                        raise RuntimeError("Session not initialized")
                    assert self.session is not None
                    response = await self.session.get(
                        f"{self.base_url}/teams/{team_id}"
                    )
                    response.raise_for_status()
                    data = response.json()

                    return Team(
                        team_id=str(data["id"]),
                        name=data["name"],
                        league=data.get("area", {}).get("name", "Unknown"),
                        season="2023-24",  # 默认当前赛季
                        founded=data.get("founded"),
                        venue=data.get("venue"),
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch team {team_id}", error=str(e))
                    # 返回占位数据以保持系统稳定
                    return Team(
                        team_id=team_id,
                        name=f"Team_{team_id}",
                        league="Unknown",
                        season="2023-24",
                    )

            # 并发执行所有API调用, 限制并发数量以避免API限流
            semaphore = asyncio.Semaphore(5)  # 最多5个并发请求

            async def bounded_fetch(team_id: str) -> Team:
                async with semaphore:
                    return await fetch_team_info(team_id)

            # 并发收集所有球队信息
            tasks = [bounded_fetch(team_id) for team_id in team_ids]
            teams = await asyncio.gather(*tasks, return_exceptions=False)

            # 过滤掉可能的异常结果
            teams = [team for team in teams if isinstance(team, Team)]

        except Exception as e:
            logger.error("Failed to collect team info", error=str(e))
            raise

        logger.info("Successfully collected team info", count=len(teams))
        return teams
