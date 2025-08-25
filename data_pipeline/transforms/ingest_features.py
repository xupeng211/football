import argparse
import logging
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

from data_pipeline.transforms.feature_engineer import generate_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_source_data(db_conn_str: str) -> pd.DataFrame:
    """Fetches all odds data from the database."""
    query = "SELECT match_id, bookmaker, home_odds, draw_odds, away_odds FROM odds;"
    try:
        with psycopg2.connect(db_conn_str) as conn:
            df = pd.read_sql_query(query, conn)
            logger.info(f"Fetched {len(df)} odds records from the database.")
            return df
    except psycopg2.Error as e:
        logger.error(f"Database error during source data fetch: {e}")
        return pd.DataFrame()


def ingest_features_data(features_df: pd.DataFrame, db_conn_str: str):
    """
    Ingests features into the features table using an UPSERT operation.
    """
    if features_df.empty:
        logger.info("No features to ingest.")
        return 0, 0

    upsert_sql = """
    INSERT INTO features (
        match_id, implied_prob_home, implied_prob_draw, implied_prob_away,
        bookie_margin, odds_spread_home, fav_flag, log_home, log_away,
        odds_ratio, prob_diff
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (match_id)
    DO UPDATE SET
        implied_prob_home = EXCLUDED.implied_prob_home,
        implied_prob_draw = EXCLUDED.implied_prob_draw,
        implied_prob_away = EXCLUDED.implied_prob_away,
        bookie_margin = EXCLUDED.bookie_margin,
        odds_spread_home = EXCLUDED.odds_spread_home,
        fav_flag = EXCLUDED.fav_flag,
        log_home = EXCLUDED.log_home,
        log_away = EXCLUDED.log_away,
        odds_ratio = EXCLUDED.odds_ratio,
        prob_diff = EXCLUDED.prob_diff;
    """

    try:
        with psycopg2.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                execute_batch(cur, upsert_sql, features_df.to_records(index=False).tolist())
                affected_rows = cur.rowcount
            conn.commit()
            logger.info(f"Successfully ingested/updated {affected_rows} feature records.")
            return affected_rows, 0
    except psycopg2.Error as e:
        logger.error(f"Database error during feature ingestion: {e}")
        return 0, len(features_df)


def main():
    # Parser is kept for future arguments, but not used for now.
    argparse.ArgumentParser(description="Generate and ingest features.").parse_args()

    db_conn_str = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/sports"
    )

    logger.info("Starting feature generation and ingestion process.")
    # 1. Fetch source data
    odds_df = fetch_source_data(db_conn_str)
    if odds_df.empty:
        logger.warning("Source data is empty. Exiting.")
        return

    # 2. Generate features
    features_df = generate_features(odds_df)
    if features_df is None or features_df.empty:
        logger.warning("Feature generation resulted in no data. Exiting.")
        return

    # 3. Ingest features
    affected, discarded = ingest_features_data(features_df, db_conn_str)

    logger.info("Feature ingestion summary:")
    logger.info(f"  - Affected (Inserted/Updated): {affected}")
    logger.info(f"  - Discarded: {discarded}")


if __name__ == "__main__":
    main()
