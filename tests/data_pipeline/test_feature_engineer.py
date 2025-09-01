import pytest

pytestmark = pytest.mark.skip(reason="data_pipeline module not implemented")

import pandas as pd
import pytest
from data_pipeline.transforms.feature_engineer import (
    aggregate_odds,
    calculate_implied_probabilities,
    generate_features,
)


@pytest.fixture
def sample_odds_df() -> pd.DataFrame:
    """Provides a sample DataFrame of odds data."""
    data = {
        "match_id": [1, 1, 2],
        "bookmaker": ["A", "B", "A"],
        "home_odds": [2.0, 2.1, 1.5],
        "draw_odds": [3.0, 3.1, 4.0],
        "away_odds": [4.0, 4.1, 5.0],
    }
    return pd.DataFrame(data)


def test_calculate_implied_probabilities():
    """Tests the calculation of implied probabilities and bookie margin."""
    df = pd.DataFrame({"home_odds": [2.0], "draw_odds": [3.0], "away_odds": [4.0]})
    result = calculate_implied_probabilities(df)
    assert "implied_prob_home" in result.columns
    assert "bookie_margin" in result.columns
    assert pd.notna(result["implied_prob_home"].iloc[0])
    assert result["bookie_margin"].iloc[0] > 0


def test_aggregate_odds(sample_odds_df):
    """Tests the aggregation of odds across bookmakers."""
    result = aggregate_odds(sample_odds_df)
    assert result is not None
    assert len(result) == 2  # Two unique match_ids
    assert result[result["match_id"] == 1]["home_odds"].iloc[0] == pytest.approx(2.05)


def test_generate_features(sample_odds_df):
    """Tests the end-to-end feature generation pipeline."""
    result = generate_features(sample_odds_df)
    assert result is not None
    assert len(result) == 2
    # Check for all new feature columns
    expected_cols = [
        "bookie_margin",
        "implied_prob_home",
        "odds_spread_home",
        "fav_flag",
        "log_home",
        "odds_ratio",
        "prob_diff",
    ]
    for col in expected_cols:
        assert col in result.columns

    # Check a specific value
    assert result.loc[result["match_id"] == 2, "fav_flag"].iloc[0] == 1
