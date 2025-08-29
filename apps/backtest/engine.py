"""
回测引擎 - 评估预测模型在历史数据上的表现
"""

import os
from dataclasses import dataclass
from datetime import date

import pandas as pd
import psycopg2
import structlog
from dotenv import load_dotenv
from sklearn.metrics import accuracy_score

from models.predictor import Predictor, _create_feature_vector

logger = structlog.get_logger()


@dataclass
class BacktestResult:
    """Backtest result data class."""

    strategy_name: str
    start_date: date
    end_date: date
    total_matches: int
    total_predictions: int
    accuracy: float
    roi: float
    net_profit: float
    model_version: str


class BacktestEngine:
    """Backtest engine for evaluating models on historical data."""

    def run_backtest(
        self,
        predictor: Predictor,
        historical_data: pd.DataFrame,
        start_date: date,
        end_date: date,
        strategy_name: str = "default",
        min_confidence: float = 0.5,
        stake_per_bet: float = 10.0,
    ) -> BacktestResult:
        """Runs a backtest for a given predictor and historical data."""
        logger.info(
            "Starting backtest",
            strategy=strategy_name,
            model_version=predictor.model_version,
        )

        # 1. Filter data for the backtest period
        test_data = historical_data[
            (historical_data["date"].dt.date >= start_date)
            & (historical_data["date"].dt.date <= end_date)
        ].copy()
        if test_data.empty:
            raise ValueError("No data available for the selected backtest period.")

        # 2. Generate predictions
        predictions = self._generate_predictions(predictor, test_data)

        # 3. Filter by confidence
        confident_predictions = predictions[
            predictions["confidence"] >= min_confidence
        ].copy()

        # 4. Calculate PnL and Accuracy
        pnl_results = self._calculate_pnl(confident_predictions, stake_per_bet)
        accuracy = self._calculate_accuracy(confident_predictions)

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            total_matches=len(test_data),
            total_predictions=len(confident_predictions),
            accuracy=accuracy,
            roi=pnl_results["roi"],
            net_profit=pnl_results["net_profit"],
            model_version=predictor.model_version or "unknown",
        )

    def _generate_predictions(
        self, predictor: Predictor, test_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Generates predictions for the test data using the predictor."""
        prediction_results = []
        for _, row in test_data.iterrows():
            features = _create_feature_vector(row.to_dict())
            # Align columns with the model's expected features
            if predictor.feature_names:
                features = features.reindex(
                    columns=predictor.feature_names, fill_value=0
                )

            proba = predictor.model.predict_proba(features)[0]
            pred_data = {
                "match_id": row["id"],
                "actual_result": row["result"],
                "confidence": proba.max(),
                "predicted_class": proba.argmax(),
                "home_odds": row["home_odds"],
                "draw_odds": row["draw_odds"],
                "away_odds": row["away_odds"],
            }
            prediction_results.append(pred_data)

        return pd.DataFrame(prediction_results)

    def _calculate_pnl(
        self, predictions: pd.DataFrame, stake_per_bet: float
    ) -> dict[str, float]:
        """Calculates profit and loss based on prediction results."""
        if predictions.empty:
            return {"net_profit": 0.0, "roi": 0.0}

        total_stakes = len(predictions) * stake_per_bet
        net_profit = 0.0

        for _, row in predictions.iterrows():
            actual_result_int = {"H": 0, "D": 1, "A": 2}.get(row["actual_result"], -1)
            if int(row["predicted_class"]) == actual_result_int:
                odds_map = {0: "home_odds", 1: "draw_odds", 2: "away_odds"}
                odds_col = odds_map[actual_result_int]
                net_profit += stake_per_bet * (row[odds_col] - 1)
            else:
                net_profit -= stake_per_bet

        roi = net_profit / total_stakes if total_stakes > 0 else 0.0
        return {"net_profit": net_profit, "roi": roi}

    def _calculate_accuracy(self, predictions: pd.DataFrame) -> float:
        """Calculates the prediction accuracy."""
        if predictions.empty:
            return 0.0

        actuals = predictions["actual_result"].map({"H": 0, "D": 1, "A": 2})
        return accuracy_score(actuals, predictions["predicted_class"])


def load_historical_data(db_conn_str: str) -> pd.DataFrame:
    """Loads historical match and odds data from the database."""
    query = """
    SELECT
        m.id, m.date, m.result,
        o.h AS home_odds, o.d AS draw_odds, o.a AS away_odds
    FROM matches m
    JOIN odds_raw o ON m.id = o.match_id
    WHERE m.result IS NOT NULL;
    """
    with psycopg2.connect(db_conn_str) as conn:
        return pd.read_sql_query(query, conn, parse_dates=["date"])


if __name__ == "__main__":
    load_dotenv()
    db_conn_str = os.environ.get("DATABASE_URL")
    if not db_conn_str:
        raise ValueError("DATABASE_URL not found in environment variables.")

    db_conn_str_local = db_conn_str.replace("@db:", "@localhost:")

    # 1. Load the latest predictor
    predictor = Predictor()
    if predictor.model_version == "stub-default":
        logger.error("No model found, cannot run backtest.")
    else:
        # 2. Load historical data
        historical_data = load_historical_data(db_conn_str_local)

        # 3. Run backtest
        engine = BacktestEngine()
        result = engine.run_backtest(
            predictor=predictor,
            historical_data=historical_data,
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1),
        )
        print(result)
