"""
回测引擎 - 评估预测模型在历史数据上的表现
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import structlog

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

    def __init__(self) -> dict[str, Any]:
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

        # 计算准确率指标
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
            # 准确率指标
            accuracy=accuracy_metrics["accuracy"],
            precision_by_class=accuracy_metrics["precision_by_class"],
            recall_by_class=accuracy_metrics["recall_by_class"],
            # 收益指标
            total_stakes=pnl_results["total_stakes"],
            total_returns=pnl_results["total_returns"],
            net_profit=pnl_results["net_profit"],
            roi=pnl_results["roi"],
            # 风险指标
            max_drawdown=risk_metrics["max_drawdown"],
            win_rate=risk_metrics["win_rate"],
            avg_odds=risk_metrics["avg_odds"],
            # 详细数据
            daily_pnl=pnl_results["daily_pnl"],
            prediction_details=confident_predictions.to_dict("records"),
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
        """合并赔率数据"""
        # TODO: 实现赔率数据合并逻辑
        # 按match_id和时间匹配最接近的赔率

        # 占位实现 - 添加模拟赔率
        match_data["home_odds"] = 2.5
        match_data["draw_odds"] = 3.2
        match_data["away_odds"] = 2.8

        return match_data

    def _generate_predictions(
        self, model: Any, test_data: pd.DataFrame
    ) -> pd.DataFrame:
        """生成预测结果"""
        logger.info("生成预测结果", matches=len(test_data))

        # 提取特征(需要与训练时保持一致)
        # TODO: 实现特征提取逻辑
        feature_columns = [
            col
            for col in test_data.columns
            if col.startswith(("home_", "away_", "diff_"))
        ]

        if not feature_columns:
            # 生成模拟特征用于演示
            feature_columns = [
                "home_recent_form",
                "away_recent_form",
                "home_strength",
                "away_strength",
                "diff_form",
                "home_advantage",
            ]
            for col in feature_columns:
                test_data[col] = np.random.normal(0.5, 0.2, len(test_data))

        features = test_data[feature_columns].fillna(0)

        # 生成预测(占位实现)
        # TODO: 使用实际模型进行预测
        # probabilities = model.predict_proba(features)

        # 模拟预测概率
        probabilities = np.random.dirichlet([1, 1, 1], len(features))
        predicted_classes = np.argmax(probabilities, axis=1)
        max_probabilities = np.max(probabilities, axis=1)

        # 添加预测结果到数据
        test_data["predicted_class"] = predicted_classes
        test_data["confidence"] = max_probabilities
        test_data["home_win_prob"] = probabilities[:, 2]  # 主胜概率
        test_data["draw_prob"] = probabilities[:, 1]  # 平局概率
        test_data["away_win_prob"] = probabilities[:, 0]  # 客胜概率

        return test_data

    def _calculate_pnl(
        self, predictions: pd.DataFrame, stake_per_bet: float
    ) -> dict[str, Any]:
        """计算盈亏"""
        results = []
        daily_pnl = {}

        for _, row in predictions.iterrows():
            # 确定实际结果
            actual_result = self._get_actual_result(row)
            predicted_result = int(row["predicted_class"])

            # 获取对应的赔率
            if predicted_result == 2:  # 预测主胜
                odds = row["home_odds"]
                result_name = "主胜"
            elif predicted_result == 1:  # 预测平局
                odds = row["draw_odds"]
                result_name = "平局"
            else:  # 预测客胜
                odds = row["away_odds"]
                result_name = "客胜"

            # 计算盈亏
            if actual_result == predicted_result:
                pnl = stake_per_bet * (odds - 1)  # 赢了
                win = True
            else:
                pnl = -stake_per_bet  # 输了
                win = False

            # 记录结果
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

            # 按日汇总
            date_key = row["match_date"].date()
            if date_key not in daily_pnl:
                daily_pnl[date_key] = 0
            daily_pnl[date_key] += pnl

        # 计算汇总指标
        total_stakes = len(results) * stake_per_bet
        total_returns = sum(r["pnl"] for r in results) + total_stakes
        net_profit = sum(r["pnl"] for r in results)
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
        """获取实际比赛结果"""
        home_score = row.get("home_score", 0)
        away_score = row.get("away_score", 0)

        # 如果没有比分数据,生成随机结果用于演示
        if pd.isna(home_score) or pd.isna(away_score):
            return np.random.choice([0, 1, 2])  # 随机结果

        if home_score > away_score:
            return 2  # 主胜
        elif home_score == away_score:
            return 1  # 平局
        else:
            return 0  # 客胜

    def _calculate_accuracy_metrics(self, predictions: pd.DataFrame) -> dict[str, Any]:
        """计算准确率指标"""
        actual_results = []
        predicted_results = []

        for _, row in predictions.iterrows():
            actual = self._get_actual_result(row)
            predicted = int(row["predicted_class"])

            actual_results.append(actual)
            predicted_results.append(predicted)

        # 整体准确率
        correct_predictions = sum(
            1 for a, p in zip(actual_results, predicted_results, strict=False) if a == p
        )
        accuracy = correct_predictions / len(predictions) if len(predictions) > 0 else 0

        # 各类别精确率和召回率
        class_names = ["客胜", "平局", "主胜"]
        precision_by_class = {}
        recall_by_class = {}

        for class_idx, class_name in enumerate(class_names):
            # 精确率:预测为该类别且正确的 / 预测为该类别的总数
            predicted_as_class = sum(1 for p in predicted_results if p == class_idx)
            correct_as_class = sum(
                1
                for a, p in zip(actual_results, predicted_results, strict=False)
                if p == class_idx and a == class_idx
            )
            precision = (
                correct_as_class / predicted_as_class if predicted_as_class > 0 else 0
            )

            # 召回率:预测为该类别且正确的 / 实际为该类别的总数
            actual_as_class = sum(1 for a in actual_results if a == class_idx)
            recall = correct_as_class / actual_as_class if actual_as_class > 0 else 0

            precision_by_class[class_name] = precision
            recall_by_class[class_name] = recall

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
