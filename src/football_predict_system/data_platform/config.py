"""
Data Platform Configuration.
"""

from typing import Any

from pydantic import BaseModel, Field


class DataSourceConfig(BaseModel):
    """Configuration for a data source."""

    name: str
    source_type: str = Field(..., pattern="^(api|file|scraping)$")
    base_url: str | None = None
    api_key_required: bool = False
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 60
    reliability_score: float = Field(0.8, ge=0.0, le=1.0)
    is_active: bool = True

    # API specific config
    headers_template: dict[str, str] = Field(default_factory=dict)
    auth_method: str = Field("none", pattern="^(none|api_key|bearer|basic)$")


class CollectionSchedule(BaseModel):
    """Data collection schedule configuration."""

    # Daily collection
    daily_collection_cron: str = "0 */6 * * *"  # Every 6 hours
    daily_competitions: list[int] = Field(
        default_factory=lambda: [
            2021,  # Premier League
            2014,  # La Liga
            2002,  # Bundesliga
            2019,  # Serie A
            2015,  # Ligue 1
        ]
    )
    daily_date_range_days: int = 7

    # Quality monitoring
    quality_check_cron: str = "0 * * * *"  # Every hour
    quality_thresholds: dict[str, Any] = Field(
        default_factory=lambda: {
            "max_stale_hours": 24,
            "min_quality_score": 80,
            "max_missing_scores_percent": 5,
        }
    )

    # Historical backfill
    backfill_batch_days: int = 30
    backfill_delay_seconds: int = 6  # Rate limiting


class DataPlatformConfig(BaseModel):
    """Complete data platform configuration."""

    # Data sources
    football_data_org: DataSourceConfig = Field(
        default_factory=lambda: DataSourceConfig(
            name="football-data-org",
            source_type="api",
            base_url="https://api.football-data.org/v4",
            api_key_required=True,
            rate_limit_per_minute=10,  # Free tier
            headers_template={"Accept": "application/json"},
            auth_method="api_key",
            reliability_score=0.95,
        )
    )

    api_football: DataSourceConfig = Field(
        default_factory=lambda: DataSourceConfig(
            name="api-football",
            source_type="api",
            base_url="https://v3.football.api-sports.io",
            api_key_required=True,
            rate_limit_per_minute=100,  # Paid tier
            headers_template={"Accept": "application/json"},
            auth_method="api_key",
            reliability_score=0.90,
        )
    )

    # Scheduling
    schedule: CollectionSchedule = Field(default_factory=CollectionSchedule)

    # Storage settings
    max_batch_size: int = 1000
    data_retention_days: int = 365 * 3  # 3 years
    backup_enabled: bool = True
    backup_frequency_hours: int = 24

    # Quality settings
    enable_data_validation: bool = True
    enable_duplicate_detection: bool = True
    enable_anomaly_detection: bool = True

    # Performance settings
    max_concurrent_requests: int = 5
    connection_pool_size: int = 10
    cache_ttl_hours: int = 1


def get_data_platform_config() -> DataPlatformConfig:
    """Get data platform configuration."""
    return DataPlatformConfig()


# Competition mappings for easy reference
COMPETITION_MAPPINGS = {
    # Top 5 European Leagues
    "premier_league": {
        "id": 2021,
        "name": "Premier League",
        "country": "England",
        "priority": 1,
    },
    "la_liga": {
        "id": 2014,
        "name": "Primera Division",
        "country": "Spain",
        "priority": 1,
    },
    "bundesliga": {
        "id": 2002,
        "name": "Bundesliga",
        "country": "Germany",
        "priority": 1,
    },
    "serie_a": {"id": 2019, "name": "Serie A", "country": "Italy", "priority": 1},
    "ligue_1": {"id": 2015, "name": "Ligue 1", "country": "France", "priority": 1},
    # European Competitions
    "champions_league": {
        "id": 2001,
        "name": "UEFA Champions League",
        "country": "Europe",
        "priority": 2,
    },
    "europa_league": {
        "id": 2018,
        "name": "UEFA Europa League",
        "country": "Europe",
        "priority": 3,
    },
    # International
    "world_cup": {
        "id": 2000,
        "name": "FIFA World Cup",
        "country": "International",
        "priority": 1,
    },
    "euros": {
        "id": 2018,
        "name": "European Championship",
        "country": "Europe",
        "priority": 1,
    },
}


# Data collection priorities
COLLECTION_PRIORITIES = {
    1: {"frequency_hours": 6, "lookback_days": 7, "quality_threshold": 0.95},
    2: {"frequency_hours": 12, "lookback_days": 14, "quality_threshold": 0.90},
    3: {"frequency_hours": 24, "lookback_days": 30, "quality_threshold": 0.85},
}
