"""
Database writer for data platform.
"""

import uuid
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from football_predict_system.core.database import get_database_manager
from football_predict_system.core.logging import get_logger
from football_predict_system.domain.models import Team

logger = get_logger(__name__)


class UpsertResult:
    """Result of upsert operation."""

    def __init__(self, inserted: int = 0, updated: int = 0, failed: int = 0):
        self.inserted = inserted
        self.updated = updated
        self.failed = failed

    @property
    def records_processed(self) -> int:
        """Total records successfully processed."""
        return self.inserted + self.updated

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary format."""
        return {
            "inserted": self.inserted,
            "updated": self.updated,
            "failed": self.failed,
        }


class DatabaseWriter:
    """Handle data storage operations."""

    def __init__(self) -> None:
        self.db_manager = get_database_manager()
        self.logger = get_logger(__name__)

    def _get_timestamp_func(self) -> str:
        """Get the appropriate timestamp function for the database type."""
        # Check if we're using SQLite via environment variable
        import os

        database_url = os.getenv("DATABASE_URL", "")
        if "sqlite" in database_url.lower():
            return "datetime('now')"
        else:
            # PostgreSQL and other databases
            return "CURRENT_TIMESTAMP"

    async def upsert_teams(self, teams_data: list[Team] | pd.DataFrame) -> UpsertResult:
        """Insert or update team data."""

        # Handle both DataFrame and list of Team objects
        if isinstance(teams_data, list):
            # Convert Team objects to DataFrame
            if not teams_data:
                return UpsertResult()

            # Convert Team objects to dict for DataFrame
            team_dicts = []
            for team in teams_data:
                if hasattr(team, "model_dump"):
                    team_dict = team.model_dump()
                elif hasattr(team, "__dict__"):
                    # Fallback for non-Pydantic objects
                    team_dict = team.__dict__
                else:
                    # Last resort - convert to dict
                    team_dict = {
                        "external_api_id": getattr(team, "external_api_id", None),
                        "name": getattr(team, "name", ""),
                        "short_name": getattr(team, "short_name", ""),
                        "tla": getattr(team, "tla", ""),
                    }
                team_dicts.append(team_dict)

            df = pd.DataFrame(team_dicts)
        else:
            # Assume DataFrame
            df = teams_data

        if df.empty:
            return UpsertResult()

        inserted = 0
        updated = 0
        failed = 0
        timestamp_func = self._get_timestamp_func()

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
                            text(f"""
                            UPDATE teams SET
                                name = :name,
                                short_name = :short_name,
                                updated_at = {timestamp_func}
                            WHERE external_api_id = :external_api_id
                            """),
                            {
                                "external_api_id": row["external_api_id"],
                                "name": row["name"],
                                "short_name": row["short_name"],
                            },
                        )
                        updated += 1
                        self.logger.info(
                            "Updated existing team",
                            team_name=row["name"],
                            external_api_id=row["external_api_id"],
                        )
                    else:
                        # Insert new team
                        team_id = str(uuid.uuid4())
                        await session.execute(
                            text(f"""
                            INSERT INTO teams (
                                id, external_api_id, name, short_name,
                                created_at, updated_at
                            ) VALUES (
                                :id, :external_api_id, :name, :short_name,
                                {timestamp_func}, {timestamp_func}
                            )
                            """),
                            {
                                "id": team_id,
                                "external_api_id": row["external_api_id"],
                                "name": row["name"],
                                "short_name": row["short_name"],
                            },
                        )
                        inserted += 1
                        self.logger.info(
                            "Inserted new team",
                            team_name=row["name"],
                            external_api_id=row["external_api_id"],
                        )

                except (SQLAlchemyError, ValueError, KeyError) as e:
                    failed += 1
                    self.logger.error(
                        "Failed to upsert team",
                        error=str(e),
                        team_name=row.get("name", "Unknown"),
                    )

            await session.commit()

        return UpsertResult(inserted=inserted, updated=updated, failed=failed)

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
                                updated_at = {self._get_timestamp_func()}
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

                except (SQLAlchemyError, ValueError, KeyError) as e:
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
            try:
                result = await session.execute(
                    text("""
                    SELECT COUNT(*) FROM matches
                    WHERE status = 'finished'
                    AND (home_score IS NULL OR away_score IS NULL)
                    """)
                )
                finished_without_scores = result.scalar()
            except Exception:
                # Matches table might not exist in CI environment
                finished_without_scores = 0

            # Check for stale data
            try:
                result = await session.execute(
                    text("""
                    SELECT EXTRACT(EPOCH FROM NOW() - MAX(updated_at))/3600
                    FROM matches WHERE status = 'in_progress'
                    """)
                )
                stale_hours = result.scalar() or 0
            except Exception:
                stale_hours = 0

            # Get last successful update - handle table not existing
            try:
                result = await session.execute(
                    text("""
                    SELECT MAX(created_at) FROM data_collection_logs
                    WHERE status = 'success'
                    """)
                )
                last_update = result.scalar()
            except Exception as e:
                # data_collection_logs table might not exist in CI environment
                self.logger.warning(f"data_collection_logs table not found: {e}")
                last_update = None

            # Total match count
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM matches"))
                total_matches = result.scalar()
            except Exception:
                total_matches = 0

            # Recent matches (last 7 days)
            try:
                result = await session.execute(
                    text("""
                    SELECT COUNT(*) FROM matches
                    WHERE match_date >= datetime('now', '-7 days')
                    """)
                )
                recent_matches = result.scalar()
            except Exception:
                recent_matches = 0

            # Teams count
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM teams"))
                teams_count = result.scalar()
            except Exception:
                teams_count = 0

            return {
                "total_matches": total_matches,
                "teams_count": teams_count,
                "finished_without_scores": finished_without_scores,
                "stale_hours": stale_hours,
                "last_update": last_update,
                "recent_matches": recent_matches,
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
