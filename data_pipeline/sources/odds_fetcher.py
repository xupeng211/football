import json
import os
from pathlib import Path
from typing import Any, cast

import requests
import structlog
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = structlog.get_logger()


def _fetch_from_api(
    start_date: str, end_date: str, api_key: str
) -> list[dict[str, Any]]:
    base_url = os.environ.get("ODDS_API_BASE_URL", "https://example-odds.local/api")
    headers = {"X-Auth-Token": api_key}
    params = {"dateFrom": start_date, "dateTo": end_date}

    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,  # Results in sleeps of 0.5, 1, 2 seconds
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    try:
        logger.info(
            "Fetching odds from API",
            base_url=base_url,
            start_date=start_date,
            end_date=end_date,
        )
        response = http.get(base_url, headers=headers, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        odds_data = cast(list[dict[str, Any]], data.get("odds", []))
        logger.info(
            "Successfully fetched odds records",
            count=len(odds_data),
        )
        return odds_data
    except requests.exceptions.RequestException as e:
        logger.error("API request failed after retries", error=str(e))
        return []


def fetch_odds(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """
    Fetches odds data from a remote API or a local sample file.

    If the FOOTBALL_API_KEY environment variable is not set or
    USE_SAMPLE_ODDS is true, it reads from 'data/samples/odds_sample.json'.
    Otherwise, it attempts to call the remote API specified by
    ODDS_API_BASE_URL.
    """
    use_sample = os.environ.get("USE_SAMPLE_ODDS", "false").lower() == "true"
    api_key = os.environ.get("FOOTBALL_API_KEY")

    if use_sample or not api_key:
        logger.info("Using local sample data for odds")
        sample_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "samples"
            / "odds_sample.json"
        )
        if not sample_path.exists():
            logger.error("Sample data not found", path=sample_path)
            return []
        with open(sample_path, encoding="utf-8") as f:
            return cast(list[dict[str, Any]], json.load(f))

    return _fetch_from_api(start_date, end_date, api_key)
