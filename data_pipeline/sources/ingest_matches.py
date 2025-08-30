from typing import Any

import psycopg2
import structlog
from psycopg2.extras import execute_batch

from data_pipeline.sources.football_api import Match

logger = structlog.get_logger(__name__)


def ingest_matches(matches: list[Match], db_conn_str: str) -> tuple[int, int]:
    """Ingests match data into the database, handling teams first."""
    if not matches:
        return 0, 0

    team_names = set()
    for match in matches:
        team_names.add(match.home_team)
        team_names.add(match.away_team)

    try:
        with psycopg2.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                # 1. Handle teams: insert new teams and get all IDs
                team_map = _handle_teams(cur, team_names)

                # 2. Prepare and insert matches
                match_data = []
                for match in matches:
                    home_id = team_map.get(match.home_team)
                    away_id = team_map.get(match.away_team)
                    if home_id and away_id:
                        match_data.append(
                            (
                                int(match.match_id),
                                match.match_date,
                                home_id,
                                away_id,
                                match.home_score,
                                match.away_score,
                                _get_result(match),
                            )
                        )

                upsert_sql = """
                INSERT INTO matches (
                    id, date, home, away, home_goals, away_goals, result
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    home_goals = EXCLUDED.home_goals,
                    away_goals = EXCLUDED.away_goals,
                    result = EXCLUDED.result;
                """
                execute_batch(cur, upsert_sql, match_data)
                affected_rows = cur.rowcount
                conn.commit()
                return affected_rows, len(matches) - affected_rows
    except Exception as e:
        logger.error("Database error during match ingestion", error=str(e))
        return 0, len(matches)


def _handle_teams(cur: Any, team_names: set[str]) -> dict[str, int]:
    """Ensures all teams exist in the DB and returns a name-to-ID map."""
    # Insert new teams
    insert_sql = "INSERT INTO teams (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;"
    execute_batch(cur, insert_sql, [(name,) for name in team_names])

    # Get all team IDs
    cur.execute("SELECT name, id FROM teams WHERE name = ANY(%s);", (list(team_names),))
    return dict(cur.fetchall())


def _get_result(match: Match) -> str | None:
    """Determines the match result from scores."""
    if match.home_score is None or match.away_score is None:
        return None
    if match.home_score > match.away_score:
        return "H"
    if match.home_score < match.away_score:
        return "A"
    return "D"
