"""
Unit tests for the odds ingestion script.
"""

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from data_pipeline.sources.ingest_odds import ingest_data, validate_odds


@pytest.mark.parametrize(
    "record, expected",
    [
        (
            {
                "match_id": 1,
                "bookmaker": "A",
                "home_odds": 1.5,
                "draw_odds": 2.5,
                "away_odds": 3.5,
            },
            True,
        ),
        (
            {
                "match_id": None,
                "bookmaker": "A",
                "home_odds": 1.5,
                "draw_odds": 2.5,
                "away_odds": 3.5,
            },
            False,
        ),
        (
            {
                "match_id": 1,
                "bookmaker": "A",
                "home_odds": -1.5,
                "draw_odds": 2.5,
                "away_odds": 3.5,
            },
            False,
        ),
        (
            {
                "match_id": 1,
                "bookmaker": "A",
                "home_odds": 1.5,
                "draw_odds": 2.5,
            },  # Missing key
            False,
        ),
    ],
)
def test_validate_odds(record: dict[str, Any], expected: bool) -> None:
    """Tests the validation of odds records."""
    assert validate_odds(record) == expected


@patch("data_pipeline.sources.ingest_odds.execute_batch")
@patch("data_pipeline.sources.ingest_odds.psycopg2")
def test_ingest_data(mock_psycopg2: MagicMock, mock_execute_batch: MagicMock) -> None:
    """Tests the data ingestion logic."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.rowcount = 2  # Simulate 2 rows affected
    mock_psycopg2.Error = getattr(sys.modules.get("psycopg2"), "Error", Exception)

    odds_data: list[dict[str, Any]] = [
        {
            "match_id": 1,
            "bookmaker": "A",
            "home_odds": 1.5,
            "draw_odds": 2.5,
            "away_odds": 3.5,
        },
        {
            "match_id": 2,
            "bookmaker": "B",
            "home_odds": 2.0,
            "draw_odds": 3.0,
            "away_odds": 4.0,
        },
        {
            "match_id": None,
            "bookmaker": "C",
            "home_odds": 2.0,
            "draw_odds": 3.0,
            "away_odds": 4.0,
        },  # Invalid
    ]

    inserted, updated, discarded = ingest_data(odds_data, "dummy_conn_str")

    mock_psycopg2.connect.assert_called_once_with("dummy_conn_str")
    assert mock_execute_batch.call_count == 1
    assert inserted == 2
    assert updated == 0
    assert discarded == 1
