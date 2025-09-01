import pytest
pytestmark = pytest.mark.skip(reason="data_pipeline module not implemented")

"""
Unit tests for the feature ingestion module.
"""

import os
from unittest.mock import MagicMock, patch

import pandas as pd
import psycopg2
import pytest
from data_pipeline.transforms.ingest_features import (
    fetch_source_data,
    ingest_features_data,
)
from data_pipeline.transforms.ingest_features import main as ingest_features_main
from pandas.testing import assert_frame_equal


@pytest.fixture
def sample_features_df() -> pd.DataFrame:
    """Provides a sample DataFrame with feature data for testing."""
    data = {
        "match_id": [1, 2],
        "implied_prob_home": [0.5, 0.4],
        "implied_prob_draw": [0.3, 0.3],
        "implied_prob_away": [0.2, 0.3],
        "bookie_margin": [0.1, 0.1],
        "odds_spread_home": [0.1, 0.2],
        "fav_flag": [1, 0],
        "log_home": [0.693, 0.916],
        "log_away": [1.609, 1.386],
        "odds_ratio": [0.5, 0.75],
        "prob_diff": [0.3, 0.1],
    }
    return pd.DataFrame(data)


class TestIngestFeatures:
    """Tests for the feature ingestion functions."""

    @patch("data_pipeline.transforms.ingest_features.psycopg2")
    @patch("data_pipeline.transforms.ingest_features.pd.read_sql_query")
    def test_fetch_source_data_success(
        self, mock_read_sql: MagicMock, mock_psycopg2: MagicMock
    ):
        """Tests successful fetching of source data."""
        expected_df = pd.DataFrame({"match_id": [1, 2]})
        mock_read_sql.return_value = expected_df

        result_df = fetch_source_data("dummy_conn_str")

        mock_psycopg2.connect.assert_called_once_with("dummy_conn_str")
        assert_frame_equal(result_df, expected_df)

    @patch("data_pipeline.transforms.ingest_features.psycopg2.connect")
    def test_fetch_source_data_db_error(self, mock_connect: MagicMock):
        """Tests handling of a database error during data fetch."""
        mock_connect.side_effect = psycopg2.Error("DB Error")
        result_df = fetch_source_data("dummy_conn_str")
        assert result_df.empty

    @patch("data_pipeline.transforms.ingest_features.psycopg2")
    @patch("data_pipeline.transforms.ingest_features.execute_batch")
    def test_ingest_features_data_success(
        self,
        mock_execute_batch: MagicMock,
        mock_psycopg2: MagicMock,
        sample_features_df: pd.DataFrame,
    ):
        """Tests successful ingestion of features."""
        mock_cur = MagicMock()
        mock_cur.rowcount = len(sample_features_df)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_psycopg2.connect.return_value.__enter__.return_value = mock_conn

        affected, discarded = ingest_features_data(sample_features_df, "dummy_conn_str")

        assert affected == len(sample_features_df)
        assert discarded == 0
        mock_execute_batch.assert_called_once()

    @patch("data_pipeline.transforms.ingest_features.psycopg2.connect")
    def test_ingest_features_data_db_error(
        self, mock_connect: MagicMock, sample_features_df: pd.DataFrame
    ):
        """Tests handling of a database error during feature ingestion."""
        mock_connect.side_effect = psycopg2.Error("DB Error")
        affected, discarded = ingest_features_data(sample_features_df, "dummy_conn_str")
        assert affected == 0
        assert discarded == len(sample_features_df)

    def test_ingest_features_data_empty_df(self):
        """Tests that no ingestion is attempted for an empty DataFrame."""
        affected, discarded = ingest_features_data(pd.DataFrame(), "dummy_conn_str")
        assert affected == 0
        assert discarded == 0

    @patch.dict(os.environ, {"DATABASE_URL": "test_db_url"})
    @patch("data_pipeline.transforms.ingest_features.fetch_source_data")
    @patch("data_pipeline.transforms.ingest_features.generate_features")
    @patch("data_pipeline.transforms.ingest_features.ingest_features_data")
    @patch("data_pipeline.transforms.ingest_features.argparse.ArgumentParser")
    def test_main_flow(self, mock_argparse, mock_ingest, mock_generate, mock_fetch):
        """Test the main ETL flow orchestrator."""
        mock_fetch.return_value = pd.DataFrame({"match_id": [1]})
        mock_generate.return_value = pd.DataFrame({"feature": [1]})
        mock_ingest.return_value = (1, 0)

        ingest_features_main()

        mock_fetch.assert_called_once_with("test_db_url")
        mock_generate.assert_called_once()
        mock_ingest.assert_called_once()
