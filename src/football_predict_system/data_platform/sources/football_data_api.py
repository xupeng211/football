"""
Football-Data.org API collector.

Free tier limitations:
- 10 requests per minute
- No commercial use
- Limited to certain competitions
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, cast

import aiohttp
import pandas as pd

from ...core.config import get_settings
from ...core.logging import get_logger
from .base import MatchDataSource, RateLimiter, TeamDataSource

logger = get_logger(__name__)


class FootballDataAPICollector(MatchDataSource, TeamDataSource):
    """Football-Data.org API data collector."""

    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__()
        self.settings = get_settings()
        self.api_key = api_key or getattr(self.settings, "football_data_api_key", None)
        self.rate_limiter = RateLimiter(calls_per_minute=10)  # Free tier limit
        self.session: aiohttp.ClientSession | None = None

    async def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch data from the source - delegates to specific methods."""
        competition_id = kwargs.get("competition_id")
        date_from = kwargs.get("date_from")
        date_to = kwargs.get("date_to")

        return await self.fetch_matches(
            competition_id=competition_id, date_from=date_from, date_to=date_to
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None:
            headers: dict[str, str] = {
                "X-Auth-Token": self.api_key or "",
                "Accept": "application/json",
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session

    async def _make_request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make rate-limited API request."""
        await self.rate_limiter.wait_if_needed()

        session = await self._get_session()
        url = f"{self.BASE_URL}/{endpoint}"

        start_time = time.time()

        try:
            async with session.get(url, params=params) as response:
                response_time = int((time.time() - start_time) * 1000)
                self.stats.api_response_time_ms = response_time

                if response.status == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(endpoint, params)

                response.raise_for_status()
                response_data = await response.json()
                return cast(dict[str, Any], response_data)

        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {e}")
            raise

    async def fetch_competitions(self) -> pd.DataFrame:
        """Fetch available competitions."""
        data = await self._make_request("competitions")

        competitions = []
        for comp in data.get("competitions", []):
            competitions.append(
                {
                    "external_api_id": comp["id"],
                    "name": comp["name"],
                    "code": comp.get("code"),
                    "country": comp.get("area", {}).get("name"),
                    "type": comp.get("type", "LEAGUE"),
                    "plan": comp.get("plan", "TIER_FOUR"),
                }
            )

        return pd.DataFrame(competitions)

    async def fetch_teams(self, competition_id: int) -> pd.DataFrame:
        """Fetch teams for a competition."""
        endpoint = f"competitions/{competition_id}/teams"
        data = await self._make_request(endpoint)

        teams = []
        for team in data.get("teams", []):
            teams.append(
                {
                    "external_api_id": team["id"],
                    "name": team["name"],
                    "short_name": team.get("shortName", team["name"][:10]),
                    "country": team.get("area", {}).get("name"),
                    "league": data.get("competition", {}).get("name"),
                    "founded_year": team.get("founded"),
                    "venue": team.get("venue"),
                    "website": team.get("website"),
                    "crest": team.get("crest"),
                }
            )

        return pd.DataFrame(teams)

    async def fetch_matches(
        self,
        competition_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> pd.DataFrame:
        """Fetch matches data."""

        # Build endpoint
        if competition_id:
            endpoint = f"competitions/{competition_id}/matches"
        else:
            endpoint = "matches"

        # Build parameters
        params = {}
        if date_from:
            params["dateFrom"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            params["dateTo"] = date_to.strftime("%Y-%m-%d")

        data = await self._make_request(endpoint, params)

        matches = []
        for match in data.get("matches", []):
            # Parse match data
            home_team = match.get("homeTeam", {})
            away_team = match.get("awayTeam", {})
            score = match.get("score", {})

            matches.append(
                {
                    "external_api_id": match["id"],
                    "competition_name": match.get("competition", {}).get("name"),
                    "season": match.get("season", {}).get("startDate", "")[:4],
                    "matchday": match.get("matchday"),
                    "home_team": home_team.get("name"),
                    "home_team_id": home_team.get("id"),
                    "away_team": away_team.get("name"),
                    "away_team_id": away_team.get("id"),
                    "match_date": match.get("utcDate"),
                    "status": match.get("status"),
                    "venue": match.get("venue"),
                    "home_score": score.get("fullTime", {}).get("home"),
                    "away_score": score.get("fullTime", {}).get("away"),
                    "home_score_ht": score.get("halfTime", {}).get("home"),
                    "away_score_ht": score.get("halfTime", {}).get("away"),
                    "result": self._determine_result(
                        score.get("fullTime", {}).get("home"),
                        score.get("fullTime", {}).get("away"),
                    ),
                    "last_updated": match.get("lastUpdated"),
                }
            )

        return pd.DataFrame(matches)

    def _parse_matches_response(self, response_data: dict) -> pd.DataFrame:
        """Parse matches response data into DataFrame format.

        Args:
            response_data: Raw API response containing matches data

        Returns:
            DataFrame with parsed match data
        """
        matches = response_data.get("matches", [])

        if not matches:
            return pd.DataFrame()

        parsed_matches = []

        for match in matches:
            # Extract basic match info
            match_data = {
                "external_api_id": match.get("id"),
                "home_team_id": match.get("homeTeam", {}).get("id"),
                "home_team": match.get("homeTeam", {}).get("name"),
                "away_team_id": match.get("awayTeam", {}).get("id"),
                "away_team": match.get("awayTeam", {}).get("name"),
                "match_date": match.get("utcDate"),
                "status": match.get("status", "").lower(),
            }

            # Extract scores if available
            score = match.get("score", {}).get("fullTime", {})
            if score:
                match_data["home_score"] = score.get("home")
                match_data["away_score"] = score.get("away")

            parsed_matches.append(match_data)

        return pd.DataFrame(parsed_matches)

    def _determine_result(
        self, home_score: int | None, away_score: int | None
    ) -> str | None:
        """Determine match result."""
        if home_score is None or away_score is None:
            return None

        if home_score > away_score:
            return "H"
        elif home_score < away_score:
            return "A"
        else:
            return "D"

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None


class FootballDataHistoryCollector:
    """Specialized collector for historical data backfill."""

    def __init__(self, api_collector: FootballDataAPICollector) -> None:
        self.api = api_collector
        self.logger = get_logger(__name__)

    async def backfill_season_data(
        self,
        competition_id: int,
        season_start: datetime,
        season_end: datetime,
        batch_size_days: int = 30,
    ) -> list[pd.DataFrame]:
        """Backfill historical data for a complete season."""

        self.logger.info(
            "Starting historical backfill",
            competition_id=competition_id,
            season_start=season_start.date(),
            season_end=season_end.date(),
        )

        all_data = []
        current_date = season_start

        while current_date < season_end:
            batch_end = min(current_date + timedelta(days=batch_size_days), season_end)

            try:
                self.logger.info(
                    "Collecting batch",
                    date_from=current_date.date(),
                    date_to=batch_end.date(),
                )

                df = await self.api.fetch_matches(
                    competition_id=competition_id,
                    date_from=current_date,
                    date_to=batch_end,
                )

                if not df.empty:
                    all_data.append(df)
                    self.logger.info(f"Collected {len(df)} matches")

                # Add delay to respect rate limits
                await asyncio.sleep(6)  # 10 requests per minute = 6s between

            except Exception as e:
                self.logger.error(
                    "Batch collection failed",
                    date_from=current_date.date(),
                    error=str(e),
                )
                # Continue with next batch

            current_date = batch_end

        self.logger.info("Historical backfill completed", total_batches=len(all_data))

        return all_data


# Popular competition IDs for quick reference
POPULAR_COMPETITIONS = {
    "premier_league": 2021,  # English Premier League
    "la_liga": 2014,  # Spanish La Liga
    "bundesliga": 2002,  # German Bundesliga
    "serie_a": 2019,  # Italian Serie A
    "ligue_1": 2015,  # French Ligue 1
    "champions_league": 2001,  # UEFA Champions League
    "europa_league": 2018,  # UEFA Europa League
    "world_cup": 2000,  # FIFA World Cup
}
