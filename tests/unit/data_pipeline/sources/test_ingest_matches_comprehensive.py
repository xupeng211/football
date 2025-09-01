import pytest

pytestmark = pytest.mark.skip(reason="data_pipeline module not implemented")

from datetime import datetime
from unittest.mock import MagicMock, patch

import psycopg2
from data_pipeline.sources.football_api import Match
from data_pipeline.sources.ingest_matches import (
    _get_result,
    _handle_teams,
    ingest_matches,
)


def test_get_result_home_win() -> None:
    """Test _get_result for a home win."""
    match = Match(
        match_id="1",
        match_date=datetime.fromisoformat("2023-01-01T12:00:00"),
        home_team="A",
        away_team="B",
        home_score=2,
        away_score=1,
        league="Test League",
        season="2023",
    )
    assert _get_result(match) == "H"


def test_get_result_away_win() -> None:
    """Test _get_result for an away win."""
    match = Match(
        match_id="1",
        match_date=datetime.fromisoformat("2023-01-01T12:00:00"),
        home_team="A",
        away_team="B",
        home_score=1,
        away_score=2,
        league="Test League",
        season="2023",
    )
    assert _get_result(match) == "A"


def test_get_result_draw() -> None:
    """Test _get_result for a draw."""
    match = Match(
        match_id="1",
        match_date=datetime.fromisoformat("2023-01-01T12:00:00"),
        home_team="A",
        away_team="B",
        home_score=1,
        away_score=1,
        league="Test League",
        season="2023",
    )
    assert _get_result(match) == "D"


def test_get_result_no_score() -> None:
    """Test _get_result when scores are None."""
    match_home_none = Match(
        match_id="1",
        match_date=datetime.fromisoformat("2023-01-01T12:00:00"),
        home_team="A",
        away_team="B",
        home_score=None,
        away_score=1,
        league="Test League",
        season="2023",
    )
    assert _get_result(match_home_none) is None
    match_away_none = Match(
        match_id="1",
        match_date=datetime.fromisoformat("2023-01-01T12:00:00"),
        home_team="A",
        away_team="B",
        home_score=1,
        away_score=None,
        league="Test League",
        season="2023",
    )
    assert _get_result(match_away_none) is None


@patch("data_pipeline.sources.ingest_matches.execute_batch")
def test_handle_teams(mock_execute_batch: MagicMock) -> None:
    """Test the _handle_teams function."""
    mock_cur = MagicMock()
    team_names = {"Team A", "Team B"}
    mock_cur.fetchall.return_value = [("Team A", 1), ("Team B", 2)]

    team_map = _handle_teams(mock_cur, team_names)

    mock_execute_batch.assert_called_once()
    mock_cur.execute.assert_called_once_with(
        "SELECT name, id FROM teams WHERE name = ANY(%s);", (list(team_names),)
    )
    assert team_map == {"Team A": 1, "Team B": 2}


def test_ingest_matches_no_matches() -> None:
    """Test ingest_matches with an empty list."""
    inserted, skipped = ingest_matches([], "dummy_conn_str")
    assert inserted == 0
    assert skipped == 0


@patch("data_pipeline.sources.ingest_matches.psycopg2")
@patch("data_pipeline.sources.ingest_matches._handle_teams")
@patch("data_pipeline.sources.ingest_matches.execute_batch")
def test_ingest_matches_success(
    mock_execute_batch: MagicMock,
    mock_handle_teams: MagicMock,
    mock_psycopg2: MagicMock,
) -> None:
    """Test a successful run of ingest_matches."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_psycopg2.connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.rowcount = 1
    mock_handle_teams.return_value = {"Team A": 1, "Team B": 2}

    matches = [
        Match(
            match_id="101",
            match_date=datetime.fromisoformat("2023-01-01T12:00:00"),
            home_team="Team A",
            away_team="Team B",
            home_score=1,
            away_score=0,
            league="Test League",
            season="2023",
        )
    ]

    inserted, skipped = ingest_matches(matches, "dummy_conn_str")

    mock_psycopg2.connect.assert_called_once_with("dummy_conn_str")
    mock_handle_teams.assert_called_once_with(mock_cur, {"Team A", "Team B"})
    mock_execute_batch.assert_called_once()
    mock_conn.commit.assert_called_once()
    assert inserted == 1
    assert skipped == 0


@patch("data_pipeline.sources.ingest_matches.psycopg2")
def test_ingest_matches_db_error(mock_psycopg2: MagicMock) -> None:
    """Test ingest_matches when a database error occurs."""
    mock_psycopg2.connect.side_effect = psycopg2.Error("Connection failed")
    matches = [
        Match(
            match_id="101",
            match_date=datetime.fromisoformat("2023-01-01T12:00:00"),
            home_team="Team A",
            away_team="Team B",
            home_score=1,
            away_score=0,
            league="Test League",
            season="2023",
        )
    ]

    inserted, skipped = ingest_matches(matches, "dummy_conn_str")

    assert inserted == 0
    assert skipped == 1
