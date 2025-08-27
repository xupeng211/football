"""
XGBoost训练脚本

训练足球比赛结果预测的XGBoost多分类模型
"""

import json
import pickle  # nosec B403
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, log_loss
from sklearn.model_selection import train_test_split

from data_pipeline.features.build import build_match_features
from data_pipeline.ingest.csv_adapter import (
    create_sample_match_source,
    create_sample_odds_source,
)


def load_training_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """加载训练数据"""
    # 从样例数据加载
    matches_source = create_sample_match_source()
    odds_source = create_sample_odds_source()

    matches_df = matches_source.fetch()
    odds_df = odds_source.fetch()

    return matches_df, odds_df


def prepare_features(matches_df: pd.DataFrame, odds_df: pd.DataFrame) -> pd.DataFrame:
    """准备特征数据"""
    try:
        features_df = build_match_features(matches_df, odds_df)
        return features_df
    except Exception as e:
        print(f"特征构建失败,使用简化版本: {e}")

        # 简化版本的特征构建
        df = matches_df.merge(odds_df, left_on="id", right_on="match_id", how="left")

        # 基础特征
        df["prob_h"] = 1 / df["h"]
        df["prob_d"] = 1 / df["d"]
        df["prob_a"] = 1 / df["a"]

        # 标准化概率
        total_prob = df["prob_h"] + df["prob_d"] + df["prob_a"]
        df["prob_h_norm"] = df["prob_h"] / total_prob
        df["prob_d_norm"] = df["prob_d"] / total_prob
        df["prob_a_norm"] = df["prob_a"] / total_prob

        # 目标变量
        df["target"] = df["result"].map({"H": 0, "D": 1, "A": 2})

        # 选择特征列
        feature_cols = [
            "prob_h",
            "prob_d",
            "prob_a",
            "prob_h_norm",
            "prob_d_norm",
            "prob_a_norm",
        ]
        df = df[[*feature_cols, "target"]].dropna()

        return df


def train_xgboost_model(
    X: pd.DataFrame, y: pd.Series, model_config: dict[str, Any] | None = None
) -> xgb.XGBClassifier:
    """训练XGBoost模型"""
    if model_config is None:
        model_config = {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "objective": "multi:softprob",
            "num_class": 3,
        }

    model = xgb.XGBClassifier(**model_config)
    model.fit(X, y)

    return model


def evaluate_model(
    model: xgb.XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series
) -> dict[str, Any]:
    """评估模型性能"""
    # 预测
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    # 计算指标
    accuracy = accuracy_score(y_test, y_pred)
    logloss = log_loss(y_test, y_pred_proba)

    # 分类报告
    class_report = classification_report(
        y_test, y_pred, target_names=["Home", "Draw", "Away"], output_dict=True
    )

    metrics = {
        "accuracy": float(accuracy),
        "log_loss": float(logloss),
        "classification_report": class_report,
        "feature_importance": dict(
            zip(X_test.columns, model.feature_importances_, strict=False)
        ),
        "n_samples_train": len(X_test),
        "n_features": len(X_test.columns),
    }

    return metrics


def save_model_and_metrics(
    model: xgb.XGBClassifier, metrics: dict[str, Any], model_dir: str = "models"
) -> str:
    """保存模型和指标"""
    # 创建带时间戳的模型版本
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version = f"xgb_{timestamp}"

    # 创建模型目录
    model_path = Path(model_dir) / version
    model_path.mkdir(parents=True, exist_ok=True)

    # 保存模型
    model_file = model_path / "model.pkl"
    with open(model_file, "wb") as f:
        pickle.dump(model, f)

    # 保存指标
    metrics_file = model_path / "metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"模型已保存至: {model_path}")
    print(f"模型版本: {version}")
    print(f"准确率: {metrics['accuracy']:.4f}")
    print(f"对数损失: {metrics['log_loss']:.4f}")

    return version


def main() -> None:
    """主训练流程"""
    print("开始训练XGBoost模型...")

    try:
        # 1. 加载数据
        print("加载训练数据...")
        matches_df, odds_df = load_training_data()
        print(f"比赛数据: {len(matches_df)} 条")
        print(f"赔率数据: {len(odds_df)} 条")

        # 2. 准备特征
        print("构建特征...")
        features_df = prepare_features(matches_df, odds_df)
        print(f"特征数据: {features_df.shape}")

        # 分离特征和目标
        X = features_df.drop("target", axis=1)
        y = features_df["target"]

        print(f"特征列: {list(X.columns)}")
        print(f"目标分布: \n{y.value_counts()}")

        # 3. 划分训练测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # 4. 训练模型
        print("训练模型...")
        model = train_xgboost_model(X_train, y_train)

        # 5. 评估模型
        print("评估模型...")
        metrics = evaluate_model(model, X_test, y_test)

        # 6. 保存模型
        version = save_model_and_metrics(model, metrics)

        print("训练完成!")
        # return version

    except Exception as e:
        print(f"训练失败: {e}")
        raise


if __name__ == "__main__":
    main()
