"""
CSV数据源适配器

实现从CSV文件读取比赛和赔率数据
"""

import os
from pathlib import Path

import pandas as pd
import structlog
from dotenv import load_dotenv
from sqlalchemy import create_engine

from apps.api.core.logging import setup_logging

logger = structlog.get_logger()


def ingest_csv_data() -> None:
    """Reads sample CSVs and ingests them into the database."""
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set.")
        return

    # Adjust for local execution vs. Docker
    db_url_local = db_url.replace("@db:", "@localhost:")
    engine = create_engine(db_url_local)

    # Define sample data paths relative to the project root
    project_root = Path(__file__).parent.parent.parent
    matches_path = project_root / "sql" / "sample" / "matches.csv"
    odds_path = project_root / "sql" / "sample" / "odds.csv"

    try:
        # Ingest matches.csv
        logger.info(f"Reading matches data from {matches_path}...")
        matches_df = pd.read_csv(matches_path)
        matches_df.to_sql("matches", engine, if_exists="append", index=False)
        logger.info(
            "Successfully ingested records into table.",
            records=len(matches_df),
            table="matches",
        )

        # Ingest odds.csv
        logger.info(f"Reading odds data from {odds_path}...")
        odds_df = pd.read_csv(odds_path)
        odds_df.to_sql("odds", engine, if_exists="append", index=False)
        logger.info(
            "Successfully ingested records into table.",
            records=len(odds_df),
            table="odds",
        )

    except FileNotFoundError as e:
        logger.error(
            f"CSV file not found: {e}. Make sure you are running from the project root."
        )
    except Exception as e:
        logger.error(f"An error occurred during data ingestion: {e}")


if __name__ == "__main__":
    setup_logging()
    ingest_csv_data()
