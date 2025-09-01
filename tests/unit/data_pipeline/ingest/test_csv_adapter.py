"""
Unit tests for the CSV data adapter.
"""

import os
from unittest.mock import patch

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from data_pipeline.ingest.csv_adapter import ingest_csv_data


@pytest.fixture
def mock_db_and_fs(tmp_path):
    """Mocks database and filesystem dependencies for tests."""
    # Create dummy CSV files
    matches_csv = tmp_path / "matches.csv"
    odds_csv = tmp_path / "odds.csv"
    matches_df = pd.DataFrame(
        {
            "id": [1],
            "date": ["2024-01-01"],
            "home": [1],
            "away": [2],
            "home_goals": [1],
            "away_goals": [0],
            "result": ["H"],
        }
    )
    odds_df = pd.DataFrame(
        {
            "id": [1],
            "match_id": [1],
            "h": [1.5],
            "d": [3.0],
            "a": [2.0],
            "provider": ["bet365"],
        }
    )
    matches_df.to_csv(matches_csv, index=False)
    odds_df.to_csv(odds_csv, index=False)

    db_url = f"sqlite:///{tmp_path / 'test.db'}"

    # Patch env var and Path to redirect file access to tmp_path
    with (
        patch.dict(os.environ, {"DATABASE_URL": db_url}),
        patch("data_pipeline.ingest.csv_adapter.Path") as mock_path,
    ):
        # Configure the mock to return paths within the tmp_path fixture
        mock_path.return_value.parent.parent.parent = tmp_path
        # Since the original code does `project_root / "sql" / "sample" / ...`
        # we need to create this structure in tmp_path
        (tmp_path / "sql" / "sample").mkdir(parents=True, exist_ok=True)
        matches_csv_path = tmp_path / "sql" / "sample" / "matches.csv"
        matches_df.to_csv(matches_csv_path, index=False)
        odds_csv_path = tmp_path / "sql" / "sample" / "odds.csv"
        odds_df.to_csv(odds_csv_path, index=False)

        yield db_url


def test_ingest_csv_data_success(mock_db_and_fs):
    """Tests successful data ingestion from CSVs into a SQLite DB."""
    db_url = mock_db_and_fs
    ingest_csv_data()

    # Verify that the data was written to the database
    engine = create_engine(db_url)
    with engine.connect() as connection:
        matches_count = connection.execute(
            text("SELECT COUNT(*) FROM matches")
        ).scalar_one()
        odds_count = connection.execute(text("SELECT COUNT(*) FROM odds")).scalar_one()
        assert matches_count == 1
        assert odds_count == 1


@patch("data_pipeline.ingest.csv_adapter.os.getenv", return_value=None)
def test_ingest_csv_data_no_db_url(mock_getenv):
    """Tests that an error is logged if DATABASE_URL is not set."""
    with patch("data_pipeline.ingest.csv_adapter.logger.error") as mock_logger_error:
        ingest_csv_data()
        mock_logger_error.assert_called_once_with(
            "DATABASE_URL environment variable not set."
        )


@patch("data_pipeline.ingest.csv_adapter.pd.read_csv", side_effect=FileNotFoundError)
@patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"})
def test_ingest_csv_data_file_not_found(mock_read_csv):
    """Tests that an error is logged if a CSV file is not found."""
    with patch("data_pipeline.ingest.csv_adapter.logger.error") as mock_logger_error:
        ingest_csv_data()
        # Check that error was logged and the message is correct
        assert mock_logger_error.called
        assert "CSV file not found" in mock_logger_error.call_args[0][0]
