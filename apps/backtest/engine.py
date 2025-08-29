"""
回测引擎 - 评估预测模型在历史数据上的表现
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import structlog
from sklearn.metrics import accuracy_score, classification_report

logger = structlog.get_logger()


@dataclass
class BacktestResult:
    """回测结果"""

    strategy_name: str
    start_date: date
    end_date: date
    total_matches: int
    total_predictions: int

    # 准确率指标
    accuracy: float
    precision_by_class: dict[str, float]  # 各类别精确率
    recall_by_class: dict[str, float]  # 各类别召回率

    # 投注收益指标
    total_stakes: float
    total_returns: float
    net_profit: float
    roi: float  # 投资回报率

    # 风险指标
    max_drawdown: float
    win_rate: float
    avg_odds: float

    # 详细记录
    daily_pnl: list[float]
    prediction_details: list[dict[str, Any]]


class BacktestEngine:
    """回测引擎"""

    def __init__(self) -> None:
        """初始化回测引擎"""
        self.results_history: list[BacktestResult] = []

    def run_backtest(
        self,
        model: Any,  # 训练好的模型
        historical_data: pd.DataFrame,  # 历史数据
        odds_data: pd.DataFrame,  # 赔率数据
        start_date: date,
        end_date: date,
        strategy_name: str = "default",
        min_confidence: float = 0.6,  # 最低置信度阈值
        stake_per_bet: float = 10.0,  # 每注金额
    ) -> BacktestResult:
        """
        运行回测

        Args:
            model: 预测模型
            historical_data: 历史比赛数据
            odds_data: 历史赔率数据
            start_date: 回测开始日期
            end_date: 回测结束日期
            strategy_name: 策略名称
            min_confidence: 最低预测置信度
            stake_per_bet: 每注投注金额

        Returns:
            回测结果
        """
        logger.info(
            "开始回测",
            strategy=strategy_name,
            start_date=str(start_date),
            end_date=str(end_date),
            min_confidence=min_confidence,
        )

        # 筛选回测期间的数据
        test_data = historical_data[
            (historical_data["match_date"].dt.date >= start_date)
            & (historical_data["match_date"].dt.date <= end_date)
        ].copy()

        if len(test_data) == 0:
            raise ValueError(f"回测期间 {start_date} 到 {end_date} 没有数据")

        # 合并赔率数据
        test_data = self._merge_odds_data(test_data, odds_data)

        # 生成预测
        predictions = self._generate_predictions(model, test_data)

        # 筛选高置信度预测
        confident_predictions = predictions[
            predictions["confidence"] >= min_confidence
        ].copy()

        logger.info(
            f"筛选出{len(confident_predictions)}个高置信度预测",
            total_matches=len(test_data),
            confident_ratio=len(confident_predictions) / len(test_data),
        )

        # 计算收益
        pnl_results = self._calculate_pnl(confident_predictions, stake_per_bet)

        accuracy_metrics = self._calculate_accuracy_metrics(confident_predictions)

        # 计算风险指标
        risk_metrics = self._calculate_risk_metrics(pnl_results)

        # 构造回测结果
        result = BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            total_matches=len(test_data),
            total_predictions=len(confident_predictions),
            accuracy=accuracy_metrics["accuracy"],
            precision_by_class=accuracy_metrics["precision_by_class"],
            recall_by_class=accuracy_metrics["recall_by_class"],
            total_stakes=pnl_results["total_stakes"],
            total_returns=pnl_results["total_returns"],
            net_profit=pnl_results["net_profit"],
            roi=pnl_results["roi"],
            max_drawdown=risk_metrics["max_drawdown"],
            win_rate=risk_metrics["win_rate"],
            avg_odds=risk_metrics["avg_odds"],
            daily_pnl=pnl_results["daily_pnl"],
            prediction_details=[
                {str(k): v for k, v in record.items()}
                for record in confident_predictions.to_dict("records")
            ],
        )

        self.results_history.append(result)

        logger.info(
            "回测完成",
            accuracy=f"{result.accuracy:.3f}",
            roi=f"{result.roi:.3f}",
            net_profit=result.net_profit,
        )

        return result

    def _merge_odds_data(
        self, match_data: pd.DataFrame, odds_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Merges historical match data with the corresponding odds."""
        # Rename odds columns for clarity and consistency
        odds_renamed = odds_data.rename(
            columns={"h": "home_odds", "d": "draw_odds", "a": "away_odds"}
        )

        # Merge based on match_id. The historical_data (match_data) uses 'id'.
        merged_data = pd.merge(
            match_data,
            odds_renamed,
            left_on="id",
            right_on="match_id",
            how="inner",
        )

        # Drop the redundant match_id column from the odds table
        return merged_data.drop(columns=["match_id"])

    def _generate_predictions(
        self, model: Any, test_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Generates predictions with real feature engineering."""
        logger.info("Generating predictions", matches=len(test_data))

        # 1. Feature Engineering (consistent with training/inference)
        features_df = test_data.copy()
        features_df["implied_prob_home"] = 1 / features_df["home_odds"]
        features_df["implied_prob_draw"] = 1 / features_df["draw_odds"]
        features_df["implied_prob_away"] = 1 / features_df["away_odds"]
        features_df["bookie_margin"] = (
            features_df["implied_prob_home"]
            + features_df["implied_prob_draw"]
            + features_df["implied_prob_away"]
            - 1
        )
        features_df["odds_spread_home"] = (
            features_df["home_odds"] - features_df["home_odds"].min()
        )
        features_df["fav_flag"] = (
            features_df["home_odds"] < features_df["away_odds"]
        ).astype(int)
        features_df["log_home"] = np.log(features_df["home_odds"])
        features_df["log_away"] = np.log(features_df["away_odds"])
        features_df["odds_ratio"] = features_df["home_odds"] / features_df["away_odds"]
        features_df["prob_diff"] = (
            features_df["implied_prob_home"] - features_df["implied_prob_away"]
        )

        feature_columns = [
            "fav_flag",
            "log_away",
            "log_home",
            "prob_diff",
            "odds_ratio",
            "bookie_margin",
            "odds_spread_home",
            "implied_prob_away",
            "implied_prob_draw",
            "implied_prob_home",
        ]
        features = features_df[feature_columns]

        # 2. Predict using the actual model
        probabilities = model.predict_proba(features)
        predicted_classes = np.argmax(probabilities, axis=1)
        max_probabilities = np.max(probabilities, axis=1)

        # 3. Append results
        # Class mapping: 0: Home, 1: Draw, 2: Away
        test_data["predicted_class"] = predicted_classes
        test_data["confidence"] = max_probabilities
        test_data["home_win_prob"] = probabilities[:, 0]
        test_data["draw_prob"] = probabilities[:, 1]
        test_data["away_win_prob"] = probabilities[:, 2]

        return test_data

    def _calculate_pnl(
        self, predictions: pd.DataFrame, stake_per_bet: float
    ) -> dict[str, Any]:
        """Calculates profit and loss."""
        results = []
        daily_pnl: dict[str, float] = {}
        # Class mapping: 0:Home, 1:Draw, 2:Away
        odds_map = {0: "home_odds", 1: "draw_odds", 2: "away_odds"}
        name_map = {0: "主胜", 1: "平局", 2: "客胜"}

        for _, row in predictions.iterrows():
            actual_result = self._get_actual_result(row)
            predicted_result = int(row["predicted_class"])

            odds_col = odds_map.get(predicted_result, "home_odds")
            odds = row[odds_col]
            result_name = name_map.get(predicted_result, "N/A")

            win = actual_result == predicted_result
            pnl = stake_per_bet * (odds - 1) if win else -stake_per_bet

            bet_result = {
                "match_id": row.get("match_id", ""),
                "match_date": row["match_date"],
                "prediction": result_name,
                "actual_result": actual_result,
                "predicted_result": predicted_result,
                "odds": odds,
                "stake": stake_per_bet,
                "pnl": pnl,
                "win": win,
                "confidence": row["confidence"],
            }
            results.append(bet_result)

            date_key = row["match_date"].date()
            daily_pnl.setdefault(date_key, 0)
            daily_pnl[date_key] += pnl

        total_stakes = len(results) * stake_per_bet
        net_profit = sum(r["pnl"] for r in results)
        total_returns = total_stakes + net_profit
        roi = net_profit / total_stakes if total_stakes > 0 else 0

        return {
            "results": results,
            "total_stakes": total_stakes,
            "total_returns": total_returns,
            "net_profit": net_profit,
            "roi": roi,
            "daily_pnl": list(daily_pnl.values()),
        }

    def _get_actual_result(self, row: pd.Series) -> int:
        """Determines the actual match outcome from scores."""
        if "home_score" in row and "away_score" in row:
            if row["home_score"] > row["away_score"]:
                return 0  # Home win
            elif row["home_score"] == row["away_score"]:
                return 1  # Draw
            else:
                return 2  # Away win
        # Fallback for safety, though data should be clean
        return int(np.random.choice([0, 1, 2]))

    def _calculate_accuracy_metrics(self, predictions: pd.DataFrame) -> dict[str, Any]:
        """Calculates accuracy metrics using sklearn."""
        if predictions.empty:
            return {
                "accuracy": 0,
                "precision_by_class": {},
                "recall_by_class": {},
            }

        actual_results = predictions.apply(self._get_actual_result, axis=1)
        predicted_results = predictions["predicted_class"]

        accuracy = accuracy_score(actual_results, predicted_results)

        # Class mapping: 0:Home, 1:Draw, 2:Away
        class_names = ["主胜", "平局", "客胜"]
        report = classification_report(
            actual_results,
            predicted_results,
            target_names=class_names,
            output_dict=True,
            zero_division=0,
        )

        precision_by_class = {name: report[name]["precision"] for name in class_names}
        recall_by_class = {name: report[name]["recall"] for name in class_names}

        return {
            "accuracy": accuracy,
            "precision_by_class": precision_by_class,
            "recall_by_class": recall_by_class,
        }

    def _calculate_risk_metrics(self, pnl_results: dict[str, Any]) -> dict[str, Any]:
        """计算风险指标"""
        results = pnl_results["results"]
        daily_pnl = pnl_results["daily_pnl"]

        if not results:
            return {"max_drawdown": 0, "win_rate": 0, "avg_odds": 0}

        # 胜率
        wins = sum(1 for r in results if r["win"])
        win_rate = wins / len(results)

        # 平均赔率
        avg_odds = np.mean([r["odds"] for r in results])

        # 最大回撤
        cumulative_pnl = np.cumsum([0, *daily_pnl])
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdowns = running_max - cumulative_pnl
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0

        return {
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "avg_odds": avg_odds,
        }

    def compare_strategies(self, strategy_names: list[str]) -> pd.DataFrame:
        """比较不同策略的回测结果"""
        if not self.results_history:
            return pd.DataFrame()

        # 筛选指定策略
        if strategy_names:
            filtered_results = [
                r for r in self.results_history if r.strategy_name in strategy_names
            ]
        else:
            filtered_results = self.results_history

        # 构造比较表格
        comparison_data = []
        for result in filtered_results:
            comparison_data.append(
                {
                    "strategy": result.strategy_name,
                    "period": f"{result.start_date} to {result.end_date}",
                    "total_matches": result.total_matches,
                    "predictions": result.total_predictions,
                    "accuracy": result.accuracy,
                    "roi": result.roi,
                    "net_profit": result.net_profit,
                    "win_rate": result.win_rate,
                    "max_drawdown": result.max_drawdown,
                }
            )

        return pd.DataFrame(comparison_data)
