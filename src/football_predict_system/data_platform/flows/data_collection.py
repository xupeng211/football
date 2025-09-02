"""
Prefect flows for data collection and processing.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from prefect import flow, task

from ...core.logging import get_logger
from ..sources.football_data_api import (
    POPULAR_COMPETITIONS,
    FootballDataAPICollector,
    FootballDataHistoryCollector,
)
from ..storage.database_writer import DatabaseWriter

logger = get_logger(__name__)


@task(name="collect-matches", retries=3, retry_delay_seconds=60)
async def collect_matches_task(
    competition_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None
) -> dict[str, Any]:
    """Task to collect match data."""

    collector = FootballDataAPICollector()

    try:
        df, stats = await collector.collect(
            competition_id=competition_id,
            date_from=date_from,
            date_to=date_to
        )

        logger.info(
            "Match collection completed",
            competition_id=competition_id,
            records=stats.records_fetched
        )

        return {
            "data": df.to_dict(orient="records") if not df.empty else [],
            "stats": stats.model_dump(),
            "competition_id": competition_id
        }

    finally:
        await collector.close()


@task(name="collect-teams", retries=2)
async def collect_teams_task(competition_id: int) -> dict[str, Any]:
    """Task to collect team data."""

    collector = FootballDataAPICollector()

    try:
        df = await collector.fetch_teams(competition_id)

        logger.info(
            "Team collection completed",
            competition_id=competition_id,
            teams_count=len(df)
        )

        return {
            "data": df.to_dict(orient="records") if not df.empty else [],
            "competition_id": competition_id
        }

    finally:
        await collector.close()


@task(name="store-matches", retries=2)
async def store_matches_task(match_data: dict[str, Any]) -> dict[str, int]:
    """Task to store match data to database."""

    if not match_data["data"]:
        return {"inserted": 0, "updated": 0, "failed": 0}

    df = pd.DataFrame(match_data["data"])
    writer = DatabaseWriter()

    result = await writer.upsert_matches(df)

    logger.info(
        "Match data stored",
        competition_id=match_data["competition_id"],
        inserted=result["inserted"],
        updated=result["updated"]
    )

    return result


@task(name="store-teams", retries=2)
async def store_teams_task(team_data: dict[str, Any]) -> dict[str, int]:
    """Task to store team data to database."""

    if not team_data["data"]:
        return {"inserted": 0, "updated": 0, "failed": 0}

    df = pd.DataFrame(team_data["data"])
    writer = DatabaseWriter()

    result = await writer.upsert_teams(df)

    logger.info(
        "Team data stored",
        competition_id=team_data["competition_id"],
        inserted=result["inserted"],
        updated=result["updated"]
    )

    return result


@flow(name="daily-data-collection", log_prints=True)
async def daily_data_collection_flow() -> dict[str, Any]:
    """Daily data collection flow."""

    # Default competitions for daily collection
    competitions = [
        POPULAR_COMPETITIONS["premier_league"],
        POPULAR_COMPETITIONS["la_liga"],
        POPULAR_COMPETITIONS["bundesliga"],
        POPULAR_COMPETITIONS["serie_a"],
        POPULAR_COMPETITIONS["ligue_1"]
    ]

    # Default date range: last 7 days
    date_range_days = 7
    date_to = datetime.utcnow()
    date_from = date_to - timedelta(days=date_range_days)

    logger.info(
        "Starting daily data collection",
        competitions=competitions,
        date_from=date_from.date(),
        date_to=date_to.date()
    )

    # Collect teams first (if needed)
    team_tasks = [
        collect_teams_task.submit(comp_id)
        for comp_id in competitions
    ]

    # Collect matches
    match_tasks = [
        collect_matches_task.submit(
            competition_id=comp_id,
            date_from=date_from,
            date_to=date_to
        )
        for comp_id in competitions
    ]

    # Wait for collection tasks
    team_results = await asyncio.gather(*[task.result() for task in team_tasks])
    match_results = await asyncio.gather(*[task.result() for task in match_tasks])

    # Store data
    team_store_tasks = [
        store_teams_task.submit(team_data)
        for team_data in team_results
    ]

    match_store_tasks = [
        store_matches_task.submit(match_data)
        for match_data in match_results
    ]

    # Wait for storage tasks
    team_store_results = await asyncio.gather(
        *[task.result() for task in team_store_tasks]
    )
    match_store_results = await asyncio.gather(
        *[task.result() for task in match_store_tasks]
    )

    # Calculate totals
    total_matches_inserted = sum(r["inserted"] for r in match_store_results)
    total_matches_updated = sum(r["updated"] for r in match_store_results)
    total_teams_inserted = sum(r["inserted"] for r in team_store_results)
    total_teams_updated = sum(r["updated"] for r in team_store_results)

    summary = {
        "competitions_processed": len(competitions),
        "matches": {
            "inserted": total_matches_inserted,
            "updated": total_matches_updated
        },
        "teams": {
            "inserted": total_teams_inserted,
            "updated": total_teams_updated
        },
        "execution_time": (datetime.utcnow() - date_from).total_seconds()
    }

    logger.info("Daily data collection completed", summary=summary)
    return summary


@flow(name="historical-backfill", log_prints=True)
async def historical_backfill_flow(
    competition_id: int,
    start_date: str,  # "2023-08-01"
    end_date: str     # "2024-05-31"
) -> dict[str, Any]:
    """Historical data backfill flow."""

    # Parse date strings
    season_start = datetime.fromisoformat(start_date)
    season_end = datetime.fromisoformat(end_date)

    logger.info(
        "Starting historical backfill",
        competition_id=competition_id,
        season_start=start_date.date(),
        season_end=end_date.date()
    )

    # Collect teams first
    team_data = await collect_teams_task(competition_id)
    team_result = await store_teams_task(team_data)

    # Collect historical matches
    collector = FootballDataAPICollector()
    history_collector = FootballDataHistoryCollector(collector)

    try:
        batch_data_list = await history_collector.backfill_season_data(
            competition_id=competition_id,
            season_start=start_date,
            season_end=end_date
        )

        # Process and store each batch
        total_inserted = 0
        total_updated = 0

        for i, df in enumerate(batch_data_list):
            batch_result = await store_matches_task({
                "data": df.to_dict(orient="records"),
                "competition_id": competition_id
            })

            total_inserted += batch_result["inserted"]
            total_updated += batch_result["updated"]

            logger.info(f"Processed batch {i+1}/{len(batch_data_list)}")

        summary = {
            "competition_id": competition_id,
            "season": f"{season_start} to {season_end}",
            "batches_processed": len(batch_data_list),
            "matches": {
                "inserted": total_inserted,
                "updated": total_updated
            },
            "teams": team_result
        }

        logger.info("Historical backfill completed", summary=summary)
        return summary

    finally:
        await collector.close()


@flow(name="data-quality-check", log_prints=True)
async def data_quality_check_flow() -> dict[str, Any]:
    """Data quality monitoring flow."""

    from ..storage.database_writer import DatabaseWriter

    writer = DatabaseWriter()
    quality_stats = await writer.get_data_quality_stats()

    # Check for issues
    issues = []

    # Check for missing scores in finished matches
    if quality_stats.get("finished_matches_without_scores", 0) > 0:
        issues.append({
            "type": "missing_scores",
            "count": quality_stats["finished_matches_without_scores"],
            "severity": "medium"
        })

    # Check for stale data
    if quality_stats.get("stale_matches_hours", 0) > 24:
        issues.append({
            "type": "stale_data",
            "hours": quality_stats["stale_matches_hours"],
            "severity": "high"
        })

    # Check data freshness
    last_update = quality_stats.get("last_successful_update")
    if last_update:
        hours_since_update = (
            datetime.utcnow() - datetime.fromisoformat(last_update)
        ).total_seconds() / 3600

        if hours_since_update > 6:
            issues.append({
                "type": "outdated_data",
                "hours_since_update": hours_since_update,
                "severity": "high" if hours_since_update > 24 else "medium"
            })

    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "quality_score": max(0, 100 - len(issues) * 10),  # Simple scoring
        "total_issues": len(issues),
        "issues": issues,
        "stats": quality_stats
    }

    if issues:
        logger.warning("Data quality issues detected", issues=issues)
    else:
        logger.info("Data quality check passed", score=result["quality_score"])

    return result
