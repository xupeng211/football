"""
Tests for the odds_fetcher module.
"""

import os
from pathlib import Path

import pytest
import requests
from data_pipeline.sources import odds_fetcher


# Fixture to manage environment variables
@pytest.fixture
def manage_env_vars():
    original_use_sample = os.environ.get("USE_SAMPLE_ODDS")
    original_api_key = os.environ.get("FOOTBALL_API_KEY")
    yield
    if original_use_sample is None:
        os.environ.pop("USE_SAMPLE_ODDS", None)
    else:
        os.environ["USE_SAMPLE_ODDS"] = original_use_sample
    if original_api_key is None:
        os.environ.pop("FOOTBALL_API_KEY", None)
    else:
        os.environ["FOOTBALL_API_KEY"] = original_api_key


def test_fetch_odds_from_sample(manage_env_vars):
    """Test fetching odds from the local sample file."""
    os.environ["USE_SAMPLE_ODDS"] = "true"
    data = odds_fetcher.fetch_odds("2024-01-01", "2024-01-02")
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["match_id"] == 1001


def test_fetch_odds_sample_file_not_found(mocker, manage_env_vars):
    """Test handling of a missing sample file."""
    os.environ["USE_SAMPLE_ODDS"] = "true"
    mocker.patch.object(Path, "exists", return_value=False)
    data = odds_fetcher.fetch_odds("2024-01-01", "2024-01-02")
    assert data == []


def test_fetch_odds_from_api_success(mocker, manage_env_vars):
    """Test fetching odds from the API successfully."""
    os.environ["USE_SAMPLE_ODDS"] = "false"
    os.environ["FOOTBALL_API_KEY"] = "fake_key"

    mock_response = mocker.Mock()
    mock_response.json.return_value = {"odds": [{"id": "api_1"}]}
    mock_response.raise_for_status.return_value = None
    mocker.patch("requests.Session.get", return_value=mock_response)

    data = odds_fetcher.fetch_odds("2024-01-01", "2024-01-02")
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "api_1"


def test_fetch_odds_from_api_failure(mocker, manage_env_vars):
    """Test handling of API request failure."""
    os.environ["USE_SAMPLE_ODDS"] = "false"
    os.environ["FOOTBALL_API_KEY"] = "fake_key"

    mocker.patch(
        "requests.Session.get",
        side_effect=requests.exceptions.RequestException("API Error"),
    )

    data = odds_fetcher.fetch_odds("2024-01-01", "2024-01-02")
    assert data == []

    data = odds_fetcher.fetch_odds("2024-01-01", "2024-01-02")
    assert data == []
