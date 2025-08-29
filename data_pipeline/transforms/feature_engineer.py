"""
Feature engineering module for odds data processing.
"""

import numpy as np
import pandas as pd


def calculate_implied_probabilities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate implied probabilities and bookie margin from odds.

    Args:
        df: DataFrame with columns 'home_odds', 'draw_odds', 'away_odds'

    Returns:
        DataFrame with added columns for implied probabilities and margin
    """
    result = df.copy()

    # Calculate implied probabilities
    result["implied_prob_home"] = 1 / result["home_odds"]
    result["implied_prob_draw"] = 1 / result["draw_odds"]
    result["implied_prob_away"] = 1 / result["away_odds"]

    # Calculate bookie margin
    result["bookie_margin"] = (
        result["implied_prob_home"]
        + result["implied_prob_draw"]
        + result["implied_prob_away"]
        - 1
    )

    return result


def aggregate_odds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate odds across multiple bookmakers for each match.

    Args:
        df: DataFrame with columns 'match_id', 'bookmaker', 'home_odds',
            'draw_odds', 'away_odds'

    Returns:
        DataFrame with aggregated odds per match
    """
    # Group by match_id and calculate mean odds
    aggregated = (
        df.groupby("match_id")
        .agg({"home_odds": "mean", "draw_odds": "mean", "away_odds": "mean"})
        .reset_index()
    )

    return aggregated


def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    End-to-end feature generation pipeline.

    Args:
        df: Raw odds DataFrame

    Returns:
        DataFrame with all engineered features
    """
    # First aggregate odds
    aggregated = aggregate_odds(df)

    # Calculate implied probabilities and margin
    with_probs = calculate_implied_probabilities(aggregated)

    # Add additional features
    result = with_probs.copy()

    # Odds spread (difference between max and min odds)
    result["odds_spread_home"] = result["home_odds"] - result["home_odds"].min()

    # Favorite flag (1 if home team is favorite, 0 otherwise)
    result["fav_flag"] = (result["home_odds"] < result["away_odds"]).astype(int)

    # Log odds
    result["log_home"] = np.log(result["home_odds"])
    result["log_away"] = np.log(result["away_odds"])

    # Odds ratio
    result["odds_ratio"] = result["home_odds"] / result["away_odds"]

    # Probability difference
    result["prob_diff"] = result["implied_prob_home"] - result["implied_prob_away"]

    # Select and order columns to match the features table schema
    feature_columns = [
        "match_id",
        "home_odds",
        "draw_odds",
        "away_odds",
        "implied_prob_home",
        "implied_prob_draw",
        "implied_prob_away",
        "bookie_margin",
        "odds_spread_home",
        "fav_flag",
        "log_home",
        "log_away",
        "odds_ratio",
        "prob_diff",
    ]

    return result[feature_columns]
