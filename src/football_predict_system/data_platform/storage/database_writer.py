"""
Database writer for data platform.
"""

import uuid
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import text

from ...core.database import get_database_manager
from ...core.logging import get_logger

logger = get_logger(__name__)


class DatabaseWriter:
    """Handle data storage operations."""

    def __init__(self) -> None:
        self.db_manager = get_database_manager()
        self.logger = get_logger(__name__)

    async def upsert_teams(self, df: pd.DataFrame) -> dict[str, int]:
        """Insert or update team data."""
        if df.empty:
            return {"inserted": 0, "updated": 0, "failed": 0}

        inserted = 0
        updated = 0
        failed = 0

        async with self.db_manager.get_async_session() as session:
            for _, row in df.iterrows():
                try:
                    # Check if team exists
                    result = await session.execute(
                        text("""
                        SELECT id FROM teams
                        WHERE external_api_id = :external_api_id
                        """),
                        {"external_api_id": row["external_api_id"]},
                    )
                    existing = result.fetchone()

                    if existing:
                        # Update existing team
                        await session.execute(
                            text("""
                            UPDATE teams SET
                                name = :name,
                                short_name = :short_name,
                                venue = :venue,
                                founded_year = :founded_year,
                                updated_at = NOW()
                            WHERE external_api_id = :external_api_id
                            """),
                            {
                                "name": row["name"],
                                "short_name": row.get("short_name"),
                                "venue": row.get("venue"),
                                "founded_year": row.get("founded_year"),
                                "external_api_id": row["external_api_id"],
                            },
                        )
                        updated += 1
                    else:
                        # Insert new team
                        await session.execute(
                            text("""
                            INSERT INTO teams (
                                id, name, short_name, venue,
                                founded_year, external_api_id
                            ) VALUES (
                                :id, :name, :short_name, :venue,
                                :founded_year, :external_api_id
                            )
                            """),
                            {
                                "id": str(uuid.uuid4()),
                                "name": row["name"],
                                "short_name": row.get("short_name"),
                                "venue": row.get("venue"),
                                "founded_year": row.get("founded_year"),
                                "external_api_id": row["external_api_id"],
                            },
                        )
                        inserted += 1

                except Exception as e:
                    self.logger.error(
                        "Failed to upsert team", team_name=row.get("name"), error=str(e)
                    )
                    failed += 1

            await session.commit()

        return {"inserted": inserted, "updated": updated, "failed": failed}

    async def upsert_matches(self, df: pd.DataFrame) -> dict[str, int]:
        """Insert or update match data."""
        if df.empty:
            return {"inserted": 0, "updated": 0, "failed": 0}

        inserted = 0
        updated = 0
        failed = 0

        async with self.db_manager.get_async_session() as session:
            for _, row in df.iterrows():
                try:
                    # Check if match exists
                    result = await session.execute(
                        text("""
                        SELECT id FROM matches
                        WHERE external_api_id = :external_api_id
                        """),
                        {"external_api_id": row["external_api_id"]},
                    )
                    existing = result.fetchone()

                    # Get team IDs
                    home_team_id = await self._get_team_id_by_external_id(
                        session, row.get("home_team_id")
                    )
                    away_team_id = await self._get_team_id_by_external_id(
                        session, row.get("away_team_id")
                    )

                    if not (home_team_id and away_team_id):
                        self.logger.warning(
                            "Skipping match - teams not found",
                            external_api_id=row["external_api_id"],
                        )
                        failed += 1
                        continue

                    match_data = {
                        "home_team_id": home_team_id,
                        "away_team_id": away_team_id,
                        "match_date": row.get("match_date"),
                        "venue": row.get("venue"),
                        "matchday": row.get("matchday"),
                        "status": row.get("status", "scheduled").lower(),
                        "home_score": row.get("home_score"),
                        "away_score": row.get("away_score"),
                        "home_score_ht": row.get("home_score_ht"),
                        "away_score_ht": row.get("away_score_ht"),
                        "result": row.get("result"),
                        "external_api_id": row["external_api_id"],
                    }

                    if existing:
                        # Update existing match
                        await session.execute(
                            text("""
                            UPDATE matches SET
                                match_date = :match_date,
                                venue = :venue,
                                matchday = :matchday,
                                status = :status,
                                home_score = :home_score,
                                away_score = :away_score,
                                home_score_ht = :home_score_ht,
                                away_score_ht = :away_score_ht,
                                result = :result,
                                updated_at = NOW()
                            WHERE external_api_id = :external_api_id
                            """),
                            match_data,
                        )
                        updated += 1
                    else:
                        # Insert new match
                        match_data["id"] = str(uuid.uuid4())
                        await session.execute(
                            text("""
                            INSERT INTO matches (
                                id, home_team_id, away_team_id, match_date,
                                venue, matchday, status, home_score, away_score,
                                home_score_ht, away_score_ht, result,
                                external_api_id
                            ) VALUES (
                                :id, :home_team_id, :away_team_id, :match_date,
                                :venue, :matchday, :status, :home_score, :away_score,
                                :home_score_ht, :away_score_ht, :result,
                                :external_api_id
                            )
                            """),
                            match_data,
                        )
                        inserted += 1

                except Exception as e:
                    self.logger.error(
                        "Failed to upsert match",
                        external_api_id=row.get("external_api_id"),
                        error=str(e),
                    )
                    failed += 1

            await session.commit()

        return {"inserted": inserted, "updated": updated, "failed": failed}

    async def _get_team_id_by_external_id(
        self, session: Any, external_id: int | None
    ) -> str | None:
        """Get internal team ID by external API ID."""
        if not external_id:
            return None

        result = await session.execute(
            text("SELECT id FROM teams WHERE external_api_id = :external_id"),
            {"external_id": external_id},
        )
        row = result.fetchone()
        return str(row[0]) if row else None

    async def get_data_quality_stats(self) -> dict[str, Any]:
        """Get data quality statistics."""
        async with self.db_manager.get_async_session() as session:
            # Count finished matches without scores
            result = await session.execute(
                text("""
                SELECT COUNT(*) FROM matches
                WHERE status = 'finished'
                AND (home_score IS NULL OR away_score IS NULL)
                """)
            )
            finished_without_scores = result.scalar()

            # Check for stale data
            result = await session.execute(
                text("""
                SELECT EXTRACT(EPOCH FROM NOW() - MAX(updated_at))/3600
                FROM matches WHERE status = 'in_progress'
                """)
            )
            stale_hours = result.scalar() or 0

            # Get last successful update
            result = await session.execute(
                text("""
                SELECT MAX(created_at) FROM data_collection_logs
                WHERE status = 'success'
                """)
            )
            last_update = result.scalar()

            # Total match count
            result = await session.execute(text("SELECT COUNT(*) FROM matches"))
            total_matches = result.scalar()

            # Recent matches (last 7 days)
            result = await session.execute(
                text("""
                SELECT COUNT(*) FROM matches
                WHERE match_date >= NOW() - INTERVAL '7 days'
                """)
            )
            recent_matches = result.scalar()

            return {
                "total_matches": total_matches,
                "recent_matches": recent_matches,
                "finished_matches_without_scores": finished_without_scores,
                "stale_matches_hours": stale_hours,
                "last_successful_update": last_update.isoformat()
                if last_update
                else None,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def log_collection_run(
        self,
        source_name: str,
        task_name: str,
        stats: dict[str, Any],
        status: str = "success",
    ) -> None:
        """Log data collection run."""
        async with self.db_manager.get_async_session() as session:
            # Get or create data source
            result = await session.execute(
                text("SELECT id FROM data_sources WHERE name = :name"),
                {"name": source_name},
            )
            source_row = result.fetchone()

            if not source_row:
                # Create new data source
                source_id = str(uuid.uuid4())
                await session.execute(
                    text("""
                    INSERT INTO data_sources (id, name, source_type)
                    VALUES (:id, :name, 'api')
                    """),
                    {"id": source_id, "name": source_name},
                )
            else:
                source_id = str(source_row[0])

            # Log the run
            await session.execute(
                text("""
                INSERT INTO data_collection_logs (
                    id, source_id, task_name, started_at, finished_at,
                    status, records_fetched, records_processed,
                    records_inserted, records_updated, records_failed,
                    api_response_time_ms, total_execution_time_ms
                ) VALUES (
                    :id, :source_id, :task_name, :started_at, :finished_at,
                    :status, :records_fetched, :records_processed,
                    :records_inserted, :records_updated, :records_failed,
                    :api_response_time_ms, :total_execution_time_ms
                )
                """),
                {
                    "id": str(uuid.uuid4()),
                    "source_id": source_id,
                    "task_name": task_name,
                    "started_at": stats.get("started_at"),
                    "finished_at": stats.get("finished_at"),
                    "status": status,
                    "records_fetched": stats.get("records_fetched", 0),
                    "records_processed": stats.get("records_processed", 0),
                    "records_inserted": stats.get("records_inserted", 0),
                    "records_updated": stats.get("records_updated", 0),
                    "records_failed": stats.get("records_failed", 0),
                    "api_response_time_ms": stats.get("api_response_time_ms", 0),
                    "total_execution_time_ms": stats.get("total_execution_time_ms", 0),
                },
            )

            await session.commit()
