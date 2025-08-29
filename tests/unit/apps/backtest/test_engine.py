"""
Unit tests for the BacktestEngine.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from apps.backtest.engine import BacktestEngine, BacktestResult


@pytest.fixture
def historical_data() -> pd.DataFrame:
    """Provides a sample DataFrame of historical match data."""
    data = {
        "date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
        "id": [1, 2, 3],
        "home_score": [1, 2, 0],  # home_win, draw, away_win
        "away_score": [0, 2, 3],
    }
    return pd.DataFrame(data)


@pytest.fixture
def odds_data() -> pd.DataFrame:
    """Provides a sample DataFrame of odds data."""
    data = {
        "match_id": [1, 2, 3],
        "home_odds": [2.0, 1.5, 3.0],
        "draw_odds": [3.0, 3.5, 2.5],
        "away_odds": [4.0, 5.5, 1.8],
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_model() -> MagicMock:
    """Provides a mock prediction model."""
    return MagicMock()


class TestBacktestEngine:
    """Tests for the BacktestEngine."""

    @pytest.fixture
    def engine(self):
        """Provides a BacktestEngine instance."""
        return BacktestEngine()

    def test_get_actual_result(self, engine):
        """Tests the determination of actual match results."""
        # 0: Home, 1: Draw, 2: Away
        assert (
            engine._get_actual_result(pd.Series({"home_score": 2, "away_score": 1}))
            == 0
        )
        assert (
            engine._get_actual_result(pd.Series({"home_score": 1, "away_score": 1}))
            == 1
        )
        assert (
            engine._get_actual_result(pd.Series({"home_score": 0, "away_score": 1}))
            == 2
        )
        # Test with missing score data (should return a random result, so we just check if it's valid)
        assert engine._get_actual_result(pd.Series({})) in [0, 1, 2]

    def test_calculate_pnl(self, engine):
        """Tests the profit and loss calculation."""
        predictions_data = {
            "match_date": pd.to_datetime(["2023-01-01", "2023-01-01"]),
            "predicted_class": [0, 2],  # Home win, Away win
            "home_score": [2, 0],
            "away_score": [1, 2],
            "home_odds": [2.5, 1.8],
            "draw_odds": [3.0, 3.0],
            "away_odds": [2.8, 3.5],
            "confidence": [0.8, 0.9],
        }
        predictions_df = pd.DataFrame(predictions_data)

        pnl_results = engine._calculate_pnl(predictions_df, stake_per_bet=10.0)

        assert pnl_results["total_stakes"] == 20.0
        # Bet 1 (Home Win): Win, PnL = 10 * (2.5 - 1) = 15
        # Bet 2 (Away Win): Win, PnL = 10 * (3.5 - 1) = 25
        assert pnl_results["net_profit"] == 40.0
        assert pnl_results["roi"] == 2.0
        assert len(pnl_results["results"]) == 2
        assert pnl_results["results"][0]["win"] is True
        assert pnl_results["results"][1]["win"] is True

    def test_run_backtest_happy_path(
        self, engine, mock_model, historical_data, odds_data
    ):
        """Tests a successful run of the backtest engine."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 3)

        # Mock the internal prediction generation to return predictable results
        predictions = pd.merge(
            historical_data, odds_data, left_on="id", right_on="match_id"
        )
        predictions["confidence"] = 0.8
        predictions["predicted_class"] = [0, 1, 2]  # home, draw, away

        with patch.object(engine, "_generate_predictions", return_value=predictions):
            result = engine.run_backtest(
                predictor=mock_model,
                historical_data=historical_data,
                start_date=start_date,
                end_date=end_date,
            )

            assert isinstance(result, BacktestResult)
            assert result.total_matches == 3
            assert result.total_predictions == 3
            assert result.strategy_name == "default"
            # Actual results: home_win (2), draw (1), away_win (0)
            # Predicted results: home_win (2), draw (1), away_win (0)
            # All correct
            assert result.accuracy == pytest.approx(1.0)
            assert result.net_profit > 0

    def test_run_backtest_no_data_in_range(
        self, engine, mock_model, historical_data, odds_data
    ):
        """Tests that an error is raised if no data is available for the date range."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        with pytest.raises(ValueError, match="没有数据"):
            engine.run_backtest(
                predictor=mock_model,
                historical_data=historical_data,
                start_date=start_date,
                end_date=end_date,
            )

    def test_calculate_accuracy_metrics(self, engine):
        """Tests the calculation of accuracy metrics."""
        predictions_data = {
            "home_score": [2, 0, 1],  # Actual: home, away, draw
            "away_score": [1, 2, 1],
            "predicted_class": [0, 1, 2],  # Predicted: home, draw, away
        }
        predictions_df = pd.DataFrame(predictions_data)
        metrics = engine._calculate_accuracy(predictions_df)

        # 1 correct prediction (home win) out of 3
        assert metrics["accuracy"] == pytest.approx(1 / 3)
        # Precision(home): 1 correct / 1 predicted = 1.0
        assert metrics["precision_by_class"]["主胜"] == pytest.approx(1.0)
        # Recall(home): 1 correct / 1 actual = 1.0
        assert metrics["recall_by_class"]["主胜"] == pytest.approx(1.0)
        # Precision(draw): 0 correct / 1 predicted = 0.0
        assert metrics["precision_by_class"]["平局"] == pytest.approx(0.0)

    def test_calculate_risk_metrics(self, engine):
        """Tests the calculation of risk metrics."""
        pnl_results = {
            "results": [
                {"win": True, "odds": 2.0},
                {"win": False, "odds": 3.0},
                {"win": True, "odds": 2.5},
            ],
            "daily_pnl": [10, -10, 15],  # Example daily PnL
        }

        metrics = engine._calculate_risk_metrics(pnl_results)

        assert metrics["win_rate"] == pytest.approx(2 / 3)
        assert metrics["avg_odds"] == pytest.approx((2.0 + 3.0 + 2.5) / 3)
        # Cumulative PnL: [0, 10, 0, 15]
        # Running Max: [0, 10, 10, 15]
        # Drawdowns: [0, 0, 10, 0]
        assert metrics["max_drawdown"] == pytest.approx(10.0)

    def test_compare_strategies(self, engine, mock_model, historical_data, odds_data):
        """Tests the comparison of different backtest strategies."""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 3)

        predictions = pd.merge(
            historical_data, odds_data, left_on="id", right_on="match_id"
        )
        predictions["confidence"] = 0.8
        predictions["predicted_class"] = [2, 1, 0]

        with patch.object(engine, "_generate_predictions", return_value=predictions):
            engine.run_backtest(
                predictor=mock_model,
                historical_data=historical_data,
                start_date=start_date,
                end_date=end_date,
                strategy_name="strat1",
            )
            engine.run_backtest(
                predictor=mock_model,
                historical_data=historical_data,
                start_date=start_date,
                end_date=end_date,
                strategy_name="strat2",
            )

        comparison_df = engine.compare_strategies(["strat1", "strat2"])
        assert len(comparison_df) == 2
        assert "strat1" in comparison_df["strategy"].values
        assert "strat2" in comparison_df["strategy"].values
