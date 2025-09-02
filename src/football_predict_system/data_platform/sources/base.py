"""
Data source base classes and interfaces.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel

from ...core.logging import get_logger

logger = get_logger(__name__)


class DataSourceError(Exception):
    """Data source related errors."""


class CollectionStats(BaseModel):
    """Data collection statistics."""

    started_at: datetime
    finished_at: datetime | None = None
    records_fetched: int = 0
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_failed: int = 0
    api_response_time_ms: int = 0
    total_execution_time_ms: int = 0
    error_message: str | None = None


class DataSource(ABC):
    """Base class for all data sources."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
        self.stats = CollectionStats(started_at=datetime.utcnow())

    @abstractmethod
    async def fetch(self, **kwargs) -> pd.DataFrame:
        """Fetch data from the source."""

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """Validate fetched data."""

    async def collect(self, **kwargs) -> tuple[pd.DataFrame, CollectionStats]:
        """Complete data collection process with stats."""
        start_time = time.time()

        try:
            self.logger.info("Starting data collection", source=self.__class__.__name__)

            # Fetch data
            df = await self.fetch(**kwargs)
            self.stats.records_fetched = len(df)

            # Validate data
            if not self.validate(df):
                raise DataSourceError("Data validation failed")

            self.stats.records_processed = len(df)
            self.stats.finished_at = datetime.utcnow()
            self.stats.total_execution_time_ms = int((time.time() - start_time) * 1000)

            self.logger.info(
                "Data collection completed",
                records=len(df),
                duration_ms=self.stats.total_execution_time_ms,
            )

            return df, self.stats

        except Exception as e:
            self.stats.finished_at = datetime.utcnow()
            self.stats.error_message = str(e)
            self.stats.total_execution_time_ms = int((time.time() - start_time) * 1000)
            self.logger.error("Data collection failed", error=str(e))
            raise DataSourceError(f"Collection failed: {e}") from e


class MatchDataSource(DataSource):
    """Base class for match data sources."""

    REQUIRED_COLUMNS = [
        "external_api_id",
        "home_team",
        "away_team",
        "match_date",
        "home_score",
        "away_score",
        "status",
    ]

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate match data structure."""
        if df.empty:
            return True

        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            self.logger.error("Missing required columns", missing=missing_cols)
            return False

        # Check data types
        numeric_cols = ["home_score", "away_score"]
        for col in numeric_cols:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                self.logger.error("Invalid data type", column=col, expected="numeric")
                return False

        return True


class OddsDataSource(DataSource):
    """Base class for odds data sources."""

    REQUIRED_COLUMNS = [
        "match_id",
        "bookmaker",
        "home_odds",
        "draw_odds",
        "away_odds",
        "odds_time",
    ]

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate odds data structure."""
        if df.empty:
            return True

        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            self.logger.error("Missing required columns", missing=missing_cols)
            return False

        # Check odds values
        odds_cols = ["home_odds", "draw_odds", "away_odds"]
        for col in odds_cols:
            if col in df.columns:
                invalid_odds = df[df[col] <= 1.0]
                if not invalid_odds.empty:
                    self.logger.error(
                        "Invalid odds values", column=col, count=len(invalid_odds)
                    )
                    return False

        return True


class TeamDataSource(DataSource):
    """Base class for team data sources."""

    REQUIRED_COLUMNS = ["external_api_id", "name", "league", "country"]

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate team data structure."""
        if df.empty:
            return True

        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            self.logger.error("Missing required columns", missing=missing_cols)
            return False

        # Check for duplicate team names within same league
        duplicates = df.groupby(["name", "league"]).size()
        if (duplicates > 1).any():
            self.logger.error("Duplicate teams found in same league")
            return False

        return True


class RateLimiter:
    """Rate limiting for API calls."""

    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.call_times: list[float] = []

    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()

        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if now - t < 60]

        # Check if we need to wait
        if len(self.call_times) >= self.calls_per_minute:
            wait_time = 61 - (now - self.call_times[0])
            if wait_time > 0:
                logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)

        self.call_times.append(now)
