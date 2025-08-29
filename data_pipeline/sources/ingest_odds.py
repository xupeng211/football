import argparse
import os
from typing import Any

import psycopg2
import structlog
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

from apps.api.core.logging import setup_logging
from data_pipeline.sources.odds_fetcher import fetch_odds

logger = structlog.get_logger()


def validate_odds(record: dict[str, Any]) -> bool:
    """Validates a single odds record."""
    required_keys = [
        "match_id",
        "bookmaker",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
    for key in required_keys:
        if key not in record or record[key] is None:
            logger.warning("Skipping record due to missing key", key=key, record=record)
            return False

    if not isinstance(record["match_id"], int) or record["match_id"] <= 0:
        logger.warning("Skipping record due to invalid match_id", record=record)
        return False

    for key in ["home_odds", "draw_odds", "away_odds"]:
        if not isinstance(record[key], int | float) or record[key] <= 0:
            logger.warning(
                "Skipping record due to invalid odds value",
                key=key,
                record=record,
            )
            return False

    return True


def ingest_data(
    odds_data: list[dict[str, Any]], db_conn_str: str
) -> tuple[int, int, int]:
    """
    Ingests validated odds data into the PostgreSQL database using an UPSERT
    operation.

    Returns:
        tuple[int, int, int]: (inserted_count, updated_count, error_count)
    """
    validated_data = [d for d in odds_data if validate_odds(d)]
    inserted_count = 0
    updated_count = 0

    if not validated_data:
        logger.info("No valid data to ingest")
        discarded_count = len(odds_data) - len(validated_data)
        return inserted_count, updated_count, discarded_count

    upsert_sql = """
    INSERT INTO odds_raw (match_id, provider, h, d, a)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (match_id, provider)
    DO UPDATE SET
        h = EXCLUDED.h,
        d = EXCLUDED.d,
        a = EXCLUDED.a;
    """

    try:
        with psycopg2.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                # psycopg2 doesn't directly return which rows were inserted vs
                # updated in a batch. A simple rowcount is the most
                # straightforward approach here.
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
                # This is an approximation. In reality, it's the total number
                # of affected rows. A more complex query would be needed to
                # distinguish inserts from updates.
                inserted_count = cur.rowcount
            conn.commit()
    except psycopg2.Error as e:
        logger.error("Database error during ingestion", error=str(e))
        return 0, 0, len(odds_data)

    return inserted_count, updated_count, len(odds_data) - len(validated_data)


def main() -> None:
    load_dotenv()  # Load environment variables from .env file
    parser = argparse.ArgumentParser(description="Fetch and ingest odds data.")
    parser.add_argument(
        "--start", required=False, help="Start date in YYYY-MM-DD format."
    )
    parser.add_argument("--end", required=False, help="End date in YYYY-MM-DD format.")
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Force the use of local sample data.",
    )
    args = parser.parse_args()

    if args.use_sample:
        os.environ["USE_SAMPLE_ODDS"] = "true"

    db_conn_str = os.environ.get("DATABASE_URL")
    if not db_conn_str:
        raise ValueError("DATABASE_URL not found in environment variables.")

    # For local script execution, connect to localhost, not the Docker service
    # name
    db_conn_str_local = db_conn_str.replace("@db:", "@localhost:")

    logger.info("Starting odds ingestion", start_date=args.start, end_date=args.end)
    raw_data = fetch_odds(args.start, args.end)
    inserted, updated, discarded = ingest_data(raw_data, db_conn_str_local)

    logger.info("Ingestion summary:")
    logger.info("  - Affected (Inserted/Updated)", count=inserted)
    logger.info("  - Discarded", count=discarded)


if __name__ == "__main__":
    setup_logging()
    main()
