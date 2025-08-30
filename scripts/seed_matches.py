import os

import psycopg2
import structlog
from dotenv import load_dotenv

logger = structlog.get_logger()


def seed_matches() -> None:
    """Seeds the matches table with sample data."""
    load_dotenv()
    db_conn_str = os.environ.get("DATABASE_URL")
    if not db_conn_str:
        raise ValueError("DATABASE_URL not found in environment variables.")

    db_conn_str_local = db_conn_str.replace("@db:", "@localhost:")

    # Sample data: match_id, date, home_team_id, away_team_id, result
    # Team IDs are hardcoded based on the initial schema inserts.
    # 1:Arsenal, 2:Chelsea, 3:Liverpool, 4:Man City, 5:Man Utd, 6:Tottenham
    matches_data = [
        (1001, "2023-08-12", 1, 2, "H"),  # Arsenal vs Chelsea
        (1002, "2023-08-13", 3, 4, "D"),  # Liverpool vs Man City
    ]

    insert_sql = """
    INSERT INTO matches (id, date, home, away, result)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING;
    """

    try:
        with psycopg2.connect(db_conn_str_local) as conn:
            with conn.cursor() as cur:
                cur.executemany(insert_sql, matches_data)
                conn.commit()
                logger.info("Successfully seeded matches table", count=cur.rowcount)
    except psycopg2.Error as e:
        logger.error("Database error during matches seeding", error=str(e))
        raise


if __name__ == "__main__":
    seed_matches()
