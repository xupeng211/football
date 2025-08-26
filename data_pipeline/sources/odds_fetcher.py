import json
import logging
import os
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_odds(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """
    Fetches odds data from a remote API or a local sample file.

    If the FOOTBALL_API_KEY environment variable is not set or USE_SAMPLE_ODDS is true,
    it reads from 'data/samples/odds_sample.json'. Otherwise, it attempts to call
    the remote API specified by ODDS_API_BASE_URL.
    """
    use_sample = os.environ.get("USE_SAMPLE_ODDS", "false").lower() == "true"
    api_key = os.environ.get("FOOTBALL_API_KEY")

    if use_sample or not api_key:
        logger.info("Using local sample data for odds.")
        sample_path = Path(__file__).parent.parent.parent / "data" / "samples" / "odds_sample.json"
        if not sample_path.exists():
            logger.error(f"Sample data not found at {sample_path}")
            return []
        with open(sample_path, encoding="utf-8") as f:
            return json.load(f)

    # API call logic (placeholder)
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
        logger.info(f"Fetching odds from {base_url} for dates {start_date} to {end_date}")
        response = http.get(base_url, headers=headers, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched {len(data.get('odds', []))} odds records.")
        return data.get("odds", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed after retries: {e}")
        return []
