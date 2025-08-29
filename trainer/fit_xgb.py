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
import structlog
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine

from apps.api.core.logging import setup_logging
from apps.api.core.settings import settings

logger = structlog.get_logger()


def load_data_from_db(db_url: str) -> pd.DataFrame:
    """从数据库加载特征和目标数据, 并解析JSONB特征."""
    try:
        engine = create_engine(db_url)
        features_query = "SELECT * FROM features;"
        matches_query = "SELECT id AS match_id, result FROM matches;"

        features_df = pd.read_sql(features_query, engine)
        matches_df = pd.read_sql(matches_query, engine)

        if features_df.empty or matches_df.empty:
            return pd.DataFrame()

        # 1. Merge features and targets first
        merged_df = pd.merge(features_df, matches_df, on="match_id", how="inner")

        # 2. Unpack the JSONB features (which are parsed as dicts)
        unpacked_features_df = pd.json_normalize(merged_df["payload_json"])

        # 3. Concatenate the unpacked features
        merged_df = pd.concat(
            [merged_df.drop("payload_json", axis=1), unpacked_features_df],
            axis=1,
        )

        # 4. Create the numerical target column
        target_map = {"H": 0, "D": 1, "A": 2}
        merged_df["target"] = merged_df["result"].map(target_map)

        # 5. Clean up and return the final DataFrame
        final_df = merged_df.drop(columns=["id", "created_at", "result"]).dropna(
            subset=["target"]
        )
        final_df["target"] = final_df["target"].astype(int)

        return final_df
    except Exception as e:
        logger.error("Failed to load data from database", error=str(e))
        raise


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
            "eval_metric": "mlogloss",
        }

    model = xgb.XGBClassifier(**model_config)
    model.fit(X, y)

    return model


def evaluate_model(
    model: xgb.XGBClassifier, X_test: pd.DataFrame, y_test: pd.Series
) -> dict[str, Any]:
    """评估模型性能"""
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    logloss = log_loss(y_test, y_pred_proba)
    # 多分类AUC (One-vs-Rest)
    auc = roc_auc_score(y_test, y_pred_proba, multi_class="ovr")

    class_report = classification_report(
        y_test, y_pred, target_names=["Home", "Draw", "Away"], output_dict=True
    )

    # 将numpy的float32转换为python的float
    feature_importance = {
        k: float(v) for k, v in zip(X_test.columns, model.feature_importances_)
    }

    metrics = {
        "accuracy": float(accuracy),
        "log_loss": float(logloss),
        "roc_auc": float(auc),
        "classification_report": class_report,
        "feature_importance": feature_importance,
        "n_samples_test": len(X_test),
        "n_features": len(X_test.columns),
    }

    return metrics


def save_model_and_metrics(
    model: xgb.XGBClassifier,
    metrics: dict[str, Any],
    model_dir: str = "models/artifacts",
) -> str:
    """保存模型和指标到指定目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version = f"xgb_{timestamp}"

    model_path = Path(model_dir) / version
    model_path.mkdir(parents=True, exist_ok=True)

    model_file = model_path / "model.pkl"
    with open(model_file, "wb") as f:
        pickle.dump(model, f)

    metrics_file = model_path / "metrics.json"
    # 确保所有数值类型都能被JSON序列化
    for key, value in metrics.items():
        if hasattr(value, "item"):
            metrics[key] = value.item()

    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    logger.info(
        "Model saved successfully",
        path=str(model_path),
        version=version,
        accuracy=metrics["accuracy"],
        roc_auc=metrics["roc_auc"],
        log_loss=metrics["log_loss"],
    )

    return version


def main() -> None:
    """主训练流程"""
    logger.info("Starting XGBoost model training...")

    try:
        logger.info("Loading feature data from database...")
        db_url_local = settings.database_url.replace("@db:", "@localhost:")
        features_df = load_data_from_db(db_url_local)
        if features_df.empty:
            logger.warning("No feature data loaded, stopping training.")
            return
        logger.info(
            "Successfully loaded data",
            records=len(features_df),
            columns=len(features_df.columns),
        )

        non_feature_cols = ["match_id", "target"]
        X = features_df.drop(columns=non_feature_cols)
        y = features_df["target"]

        logger.info(
            "Feature and target separation complete",
            feature_columns=list(X.columns),
            target_distribution=y.value_counts(normalize=True).sort_index().to_dict(),
        )

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        logger.info(
            "Dataset split complete",
            train_samples=len(X_train),
            test_samples=len(X_test),
        )

        logger.info("Training XGBoost model...")
        model = train_xgboost_model(X_train, y_train)

        logger.info("Evaluating model performance...")
        metrics = evaluate_model(model, X_test, y_test)

        logger.info("Saving model and metrics...")
        save_model_and_metrics(model, metrics)

        logger.info("Training process completed successfully!")

    except Exception as e:
        logger.error("A critical error occurred in the training pipeline", error=str(e))
        raise


if __name__ == "__main__":
    setup_logging()
    main()
