import argparse
import logging
import os
from typing import Any

import psycopg2
from psycopg2.extras import execute_batch

from data_pipeline.sources.odds_fetcher import fetch_odds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def validate_odds(record: dict[str, Any]) -> bool:
    """Validates a single odds record."""
    required_keys = ["match_id", "bookmaker", "home_odds", "draw_odds", "away_odds"]
    for key in required_keys:
        if key not in record or record[key] is None:
            logger.warning(f"Skipping record due to missing key: {key}. Record: {record}")
            return False

    if not isinstance(record["match_id"], int) or record["match_id"] <= 0:
        logger.warning(f"Skipping record due to invalid match_id. Record: {record}")
        return False

    for key in ["home_odds", "draw_odds", "away_odds"]:
        if not isinstance(record[key], int | float) or record[key] <= 0:
            logger.warning(f"Skipping record due to invalid odds value for {key}. Record: {record}")
            return False

    return True


def ingest_data(odds_data: list[dict[str, Any]], db_conn_str: str):
    """
    Ingests validated odds data into the PostgreSQL database using an UPSERT operation.
    """
    validated_data = [d for d in odds_data if validate_odds(d)]
    inserted_count = 0
    updated_count = 0

    if not validated_data:
        logger.info("No valid data to ingest.")
        return inserted_count, updated_count, len(odds_data) - len(validated_data)

    upsert_sql = """
    INSERT INTO odds (match_id, bookmaker, home_odds, draw_odds, away_odds)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (match_id, bookmaker)
    DO UPDATE SET
        home_odds = EXCLUDED.home_odds,
        draw_odds = EXCLUDED.draw_odds,
        away_odds = EXCLUDED.away_odds;
    """

    try:
        with psycopg2.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                # psycopg2 doesn't directly support returning which rows were inserted vs updated
                # in a batch. A simple rowcount is the most straightforward approach here.
                execute_batch(
                    cur,
                    upsert_sql,
                    [
                        (
                            d["match_id"],
                            d["bookmaker"],
                            d["home_odds"],
                            d["draw_odds"],
                            d["away_odds"],
                        )
                        for d in validated_data
                    ],
                )
                # This is an approximation. In reality, it's the total number of affected rows.
                # A more complex query would be needed to distinguish inserts from updates.
                inserted_count = cur.rowcount
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Database error during ingestion: {e}")
        return 0, 0, len(odds_data)

    return inserted_count, updated_count, len(odds_data) - len(validated_data)


def main():
    parser = argparse.ArgumentParser(description="Fetch and ingest odds data.")
    parser.add_argument("--start", required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD format.")
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Force the use of local sample data.",
    )
    args = parser.parse_args()

    if args.use_sample:
        os.environ["USE_SAMPLE_ODDS"] = "true"

    db_conn_str = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/sports"
    )

    logger.info(f"Starting odds ingestion for {args.start} to {args.end}")
    raw_data = fetch_odds(args.start, args.end)
    inserted, updated, discarded = ingest_data(raw_data, db_conn_str)

    logger.info("Ingestion summary:")
    logger.info(f"  - Affected (Inserted/Updated): {inserted}")
    logger.info(f"  - Discarded: {discarded}")


if __name__ == "__main__":
    main()
