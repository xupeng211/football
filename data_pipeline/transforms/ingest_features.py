import argparse
import os

import pandas as pd
import psycopg2
import structlog
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

from apps.api.core.logging import setup_logging
from data_pipeline.transforms.feature_engineer import generate_features

logger = structlog.get_logger()


def fetch_source_data(db_conn_str: str) -> pd.DataFrame:
    """Fetches all odds data from the database."""
    query = (
        "SELECT match_id, provider AS bookmaker, h AS home_odds, "
        "d AS draw_odds, a AS away_odds FROM odds;"
    )
    try:
        with psycopg2.connect(db_conn_str) as conn:
            df = pd.read_sql_query(query, conn)  # type: ignore[call-overload]
            logger.info("Fetched odds records from the database.", records=len(df))
            return df  # type: ignore[no-any-return]
    except psycopg2.Error as e:
        logger.error("Database error during source data fetch", error=str(e))
        return pd.DataFrame()


def ingest_features_data(
    features_df: pd.DataFrame, db_conn_str: str
) -> tuple[int, int]:
    """
    Ingests features into the features table using a JSONB payload.

    Returns:
        tuple[int, int]: (inserted/updated rows, error count)
    """
    if features_df.empty:
        logger.info("No features to ingest.")
        return 0, 0

    # Prepare data for JSONB insertion
    records_to_insert = []
    for _, row in features_df.iterrows():
        match_id = row["match_id"]
        # Convert all other columns to a JSON string
        payload = row.drop("match_id").to_json()
        records_to_insert.append((match_id, payload))

    upsert_sql = """
    INSERT INTO features (match_id, payload_json)
    VALUES (%s, %s)
    ON CONFLICT (match_id)
    DO UPDATE SET
        payload_json = EXCLUDED.payload_json;
    """

    try:
        with psycopg2.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                execute_batch(cur, upsert_sql, records_to_insert)
                affected_rows = cur.rowcount
            conn.commit()
            logger.info(
                "Successfully ingested/updated feature records.",
                affected_rows=affected_rows,
            )
            return affected_rows, 0
    except psycopg2.Error as e:
        logger.error("Database error during feature ingestion", error=str(e))
        return 0, len(features_df)


def main() -> None:
    load_dotenv()  # Load environment variables from .env file
    # Parser is kept for future arguments, but not used for now.
    parser = argparse.ArgumentParser(description="Generate and ingest features.")
    parser.parse_args()

    db_conn_str = os.environ.get("DATABASE_URL")
    if not db_conn_str:
        raise ValueError("DATABASE_URL not found in environment variables.")

    # For local script execution, connect to localhost, not the Docker service
    # name
    db_conn_str_local = db_conn_str.replace("@db:", "@localhost:")

    logger.info("Starting feature generation and ingestion process.")
    # 1. Fetch source data
    odds_df = fetch_source_data(db_conn_str_local)
    if odds_df.empty:
        logger.warning("Source data is empty. Exiting.")
        return

    # 2. Generate features
    features_df = generate_features(odds_df)
    if features_df is None or features_df.empty:
        logger.warning("Feature generation resulted in no data. Exiting.")
        return

    # 3. Ingest features
    affected, discarded = ingest_features_data(features_df, db_conn_str_local)

    logger.info("Feature ingestion summary:")
    logger.info("  - Affected (Inserted/Updated)", count=affected)
    logger.info("  - Discarded", count=discarded)


if __name__ == "__main__":
    setup_logging()
    main()
