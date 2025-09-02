#!/usr/bin/env python3
"""
Deploy Prefect flows for data collection.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from prefect import serve
from prefect.client.schemas.schedules import CronSchedule

from football_predict_system.data_platform.flows.data_collection import (
    daily_data_collection_flow,
    data_quality_check_flow,
    historical_backfill_flow,
)


async def deploy_flows():
    """Deploy all data collection flows."""

    # Daily data collection - run every 6 hours
    daily_deployment = await daily_data_collection_flow.to_deployment(
        name="daily-data-collection",
        description="Collect daily match and team data from Football-Data.org",
        tags=["data-collection", "daily", "production"],
        schedule=CronSchedule(cron="0 */6 * * *"),  # Every 6 hours
        parameters={
            "competitions": None,  # Use default popular competitions
            "date_range_days": 7,
        },
    )

    # Data quality check - run every hour
    quality_deployment = await data_quality_check_flow.to_deployment(
        name="data-quality-monitoring",
        description="Monitor data quality and detect issues",
        tags=["monitoring", "quality", "production"],
        schedule=CronSchedule(cron="0 * * * *"),  # Every hour
        parameters={},
    )

    # Historical backfill - manual trigger only
    backfill_deployment = await historical_backfill_flow.to_deployment(
        name="historical-backfill",
        description="Backfill historical data for specific competition/season",
        tags=["backfill", "historical", "manual"],
        schedule=None,  # Manual trigger only
        parameters={
            "competition_id": 2021,  # Premier League
            "season_start": "2023-08-01",
            "season_end": "2024-05-31",
        },
    )

    print("🚀 Deploying Prefect flows...")

    await serve(
        daily_deployment,
        quality_deployment,
        backfill_deployment,
        print_starting_urls=True,
    )


if __name__ == "__main__":
    print("📋 Football Data Platform - Flow Deployment")
    print("=" * 50)
    print("Deploying flows:")
    print("  1. Daily Data Collection (every 6 hours)")
    print("  2. Data Quality Check (every hour)")
    print("  3. Historical Backfill (manual)")
    print("=" * 50)

    asyncio.run(deploy_flows())
