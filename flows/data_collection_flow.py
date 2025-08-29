import os
from datetime import datetime, timedelta
from typing import List

from prefect import flow, task

from data_pipeline.sources.football_api import FootballAPICollector, Match
from data_pipeline.sources.ingest_matches import ingest_matches
from data_pipeline.sources.ingest_odds import ingest_data as ingest_odds_data
from data_pipeline.sources.odds_fetcher import fetch_odds


@task
async def fetch_recent_matches_task() -> List[Match]:
    """Fetches matches from the last day."""
    async with FootballAPICollector() as collector:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        return await collector.collect_matches_by_date(
            start_date=yesterday, end_date=today
        )


@task
def ingest_matches_task(matches: List[Match]) -> None:
    """Ingests matches into the database."""
    db_conn_str = os.getenv("DATABASE_URL")
    if not db_conn_str:
        raise ValueError("DATABASE_URL must be set.")
    ingest_matches(matches, db_conn_str)


@task
def fetch_and_ingest_odds_task() -> None:
    """Fetches and ingests odds data for the last day."""
    db_conn_str = os.getenv("DATABASE_URL")
    if not db_conn_str:
        raise ValueError("DATABASE_URL must be set.")
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    raw_data = fetch_odds(
        start_date=yesterday.strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d"),
    )
    ingest_odds_data(raw_data, db_conn_str)


@flow(
    name="Daily Football Data Collection",
)
async def data_collection_flow() -> None:
    """Flow to collect and ingest daily football data."""
    matches = await fetch_recent_matches_task()
    ingest_matches_task(matches)
    fetch_and_ingest_odds_task()


if __name__ == "__main__":
    data_collection_flow.serve(name="daily-data-collection")
