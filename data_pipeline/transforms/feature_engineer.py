import logging
from typing import Optional

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def calculate_implied_probabilities(odds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates implied probabilities and bookmaker margin from odds.

    Args:
        odds_df: DataFrame with columns ['match_id', 'home_odds', 'draw_odds', 'away_odds'].

    Returns:
        DataFrame with added columns for implied probabilities and margin.
    """
    if odds_df.empty:
        return pd.DataFrame()

    # Calculate inverse of odds to get raw probabilities
    odds_df["raw_prob_home"] = 1 / odds_df["home_odds"]
    odds_df["raw_prob_draw"] = 1 / odds_df["draw_odds"]
    odds_df["raw_prob_away"] = 1 / odds_df["away_odds"]

    # Sum of raw probabilities gives the total book, including margin
    odds_df["total_book"] = odds_df[["raw_prob_home", "raw_prob_draw", "raw_prob_away"]].sum(axis=1)

    # Normalize to get implied probabilities (fair odds)
    odds_df["implied_prob_home"] = odds_df["raw_prob_home"] / odds_df["total_book"]
    odds_df["implied_prob_draw"] = odds_df["raw_prob_draw"] / odds_df["total_book"]
    odds_df["implied_prob_away"] = odds_df["raw_prob_away"] / odds_df["total_book"]

    # Bookmaker's margin (over-round)
    odds_df["bookie_margin"] = (odds_df["total_book"] - 1) * 100

    return odds_df


def aggregate_odds(odds_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Averages the odds across all bookmakers for each match.

    Args:
        odds_df: DataFrame containing odds from multiple bookmakers.

    Returns:
        A DataFrame with one row per match_id, containing averaged odds.
    """
    if odds_df.empty:
        logger.warning("Cannot aggregate empty odds DataFrame.")
        return None

    required_cols = {"match_id", "home_odds", "draw_odds", "away_odds"}
    if not required_cols.issubset(odds_df.columns):
        logger.error(f"Missing required columns for aggregation. Found: {odds_df.columns}")
        return None

    # Group by match_id and calculate the mean of the odds
    agg_odds = (
        odds_df.groupby("match_id")[["home_odds", "draw_odds", "away_odds"]].mean().reset_index()
    )
    logger.info(f"Aggregated odds for {len(agg_odds)} matches.")

    return agg_odds


def generate_features(raw_odds_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Main feature generation pipeline.

    Args:
        raw_odds_df: DataFrame of raw odds data, potentially with multiple bookmakers.

    Returns:
        A DataFrame of calculated features, ready for ingestion.
    """
    # 1. Aggregate odds across bookmakers
    agg_odds_df = aggregate_odds(raw_odds_df)
    if agg_odds_df is None:
        return None

    # 2. Calculate implied probabilities and margin
    features_df = calculate_implied_probabilities(agg_odds_df)

    # 3. Add derived odds features
    # Odds spread (away - home)
    features_df["odds_spread_home"] = features_df["away_odds"] - features_df["home_odds"]

    # Favorite flag (1: home, 0: draw, -1: away)
    features_df["fav_flag"] = np.sign(features_df["away_odds"] - features_df["home_odds"]).astype(
        int
    )

    # Log of odds
    features_df["log_home"] = np.log(features_df["home_odds"])
    features_df["log_away"] = np.log(features_df["away_odds"])

    # Ratio and difference features
    features_df["odds_ratio"] = features_df["home_odds"] / features_df["away_odds"]
    features_df["prob_diff"] = features_df["implied_prob_home"] - features_df["implied_prob_away"]

    # 4. Select and rename final feature columns
    final_features = features_df[
        [
            "match_id",
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
    ]

    logger.info(f"Generated features for {len(final_features)} matches.")
    return final_features
