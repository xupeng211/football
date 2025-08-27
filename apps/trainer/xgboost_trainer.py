"""
XGBoost训练器 - 负责模型训练、验证和超参数优化
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import structlog
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score, train_test_split

logger = structlog.get_logger()


@dataclass
class TrainingConfig:
    """训练配置"""

    # XGBoost参数
    n_estimators: int = 100
    max_depth: int = 6
    learning_rate: float = 0.1
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    random_state: int = 42

    # 训练参数
    test_size: float = 0.2
    cv_folds: int = 5
    early_stopping_rounds: int = 10

    # 优化参数
    enable_hyperopt: bool = False
    hyperopt_trials: int = 50


@dataclass
class TrainingResult:
    """训练结果"""

    model: xgb.XGBClassifier
    train_score: float
    val_score: float
    test_score: float
    feature_importance: dict[str, float]
    training_time: float
    model_params: dict[str, Any]
    cv_scores: list[float]


class XGBoostTrainer:
    """XGBoost训练器"""

    def __init__(self, config: TrainingConfig | None = None):
        """
        初始化训练器

        Args:
            config: 训练配置,None时使用默认配置
        """
        self.config = config or TrainingConfig()
        self.model: xgb.XGBClassifier | None = None
        self.feature_names: list[str] = []

    def prepare_data(
        self, features: pd.DataFrame, targets: pd.Series
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        准备训练数据

        Args:
            features: 特征数据
            targets: 目标变量 (0: 客胜, 1: 平局, 2: 主胜)

        Returns:
            (X_train, X_test, y_train, y_test)
        """
        logger.info(
            "准备训练数据",
            features_shape=features.shape,
            target_distribution=targets.value_counts().to_dict(),
        )

        # 检查数据质量
        self._validate_data(features, targets)

        # 特征名称记录
        self.feature_names = list(features.columns)

        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            features,
            targets,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
            stratify=targets,
        )

        logger.info(
            "数据分割完成",
            train_size=len(X_train),
            test_size=len(X_test),
            train_target_dist=y_train.value_counts().to_dict(),
            test_target_dist=y_test.value_counts().to_dict(),
        )

        return X_train, X_test, y_train, y_test

    def _validate_data(self, features: pd.DataFrame, targets: pd.Series) -> None:
        """验证数据质量"""
        # 检查空值
        null_counts = features.isnull().sum()
        if null_counts.sum() > 0:
            logger.warning(
                "发现空值", null_features=null_counts[null_counts > 0].to_dict()
            )

        # 检查无穷值
        inf_counts = np.isinf(features.select_dtypes(include=[np.number])).sum()
        if inf_counts.sum() > 0:
            logger.warning(
                "发现无穷值", inf_features=inf_counts[inf_counts > 0].to_dict()
            )

        # 检查目标变量分布
        target_counts = targets.value_counts()
        min_class_ratio = target_counts.min() / len(targets)
        if min_class_ratio < 0.1:
            logger.warning(
                "目标变量分布不均衡",
                distribution=target_counts.to_dict(),
                min_ratio=min_class_ratio,
            )

    def train(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
    ) -> TrainingResult:
        """
        训练模型

        Args:
            X_train: 训练特征
            X_test: 测试特征
            y_train: 训练目标
            y_test: 测试目标

        Returns:
            训练结果
        """
        start_time = datetime.now()

        logger.info("开始训练XGBoost模型", config=self.config.__dict__)

        # 创建模型
        model_params = {
            "n_estimators": self.config.n_estimators,
            "max_depth": self.config.max_depth,
            "learning_rate": self.config.learning_rate,
            "subsample": self.config.subsample,
            "colsample_bytree": self.config.colsample_bytree,
            "random_state": self.config.random_state,
            "objective": "multi:softprob",  # 多分类概率
            "num_class": 3,  # 3个类别
            "eval_metric": "mlogloss",
            "early_stopping_rounds": self.config.early_stopping_rounds,
        }

        self.model = xgb.XGBClassifier(**model_params)

        # 训练模型
        eval_set = [(X_train, y_train), (X_test, y_test)]
        self.model.fit(X_train, y_train, eval_set=eval_set, verbose=False)

        # 预测和评估
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        train_score = accuracy_score(y_train, train_pred)
        test_score = accuracy_score(y_test, test_pred)

        # 交叉验证
        cv_scores = cross_val_score(
            self.model, X_train, y_train, cv=self.config.cv_folds, scoring="accuracy"
        )
        val_score = cv_scores.mean()

        # 特征重要性
        feature_importance = dict(
            zip(self.feature_names, self.model.feature_importances_, strict=False)
        )

        # 计算训练时间
        training_time = (datetime.now() - start_time).total_seconds()

        result = TrainingResult(
            model=self.model,
            train_score=train_score,
            val_score=val_score,
            test_score=test_score,
            feature_importance=feature_importance,
            training_time=training_time,
            model_params=model_params,
            cv_scores=cv_scores.tolist(),
        )

        logger.info(
            "模型训练完成",
            train_accuracy=f"{train_score:.4f}",
            test_accuracy=f"{test_score:.4f}",
            cv_accuracy=f"{val_score:.4f}",
            training_time=f"{training_time:.2f}s",
        )

        return result

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        """
        预测概率

        Args:
            features: 特征数据

        Returns:
            预测概率 (n_samples, 3) - [客胜概率, 平局概率, 主胜概率]
        """
        if self.model is None:
            raise ValueError("模型未训练,请先调用train()方法")

        return self.model.predict_proba(features)

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        """
        预测类别

        Args:
            features: 特征数据

        Returns:
            预测类别 (0: 客胜, 1: 平局, 2: 主胜)
        """
        if self.model is None:
            raise ValueError("模型未训练,请先调用train()方法")

        return self.model.predict(features)  # type: ignore[no-any-return]

    def get_feature_importance(self, top_k: int = 20) -> dict[str, float]:
        """
        获取特征重要性

        Args:
            top_k: 返回前k个重要特征

        Returns:
            特征重要性字典
        """
        if self.model is None:
            raise ValueError("模型未训练")

        importance = dict(
            zip(self.feature_names, self.model.feature_importances_, strict=False)
        )
        # 按重要性降序排列
        sorted_importance = dict(
            sorted(importance.items(), key=lambda x: x[1], reverse=True)
        )

        return dict(list(sorted_importance.items())[:top_k])

    def save_model(self, filepath: str) -> None:
        """
        保存模型

        Args:
            filepath: 保存路径
        """
        if self.model is None:
            raise ValueError("模型未训练")

        self.model.save_model(filepath)
        logger.info("模型已保存", filepath=filepath)

    def load_model(self, filepath: str) -> None:
        """
        加载模型

        Args:
            filepath: 模型文件路径
        """
        self.model = xgb.XGBClassifier()
        self.model.load_model(filepath)
        logger.info("模型已加载", filepath=filepath)

    def hyperparameter_tuning(
        self, X_train: pd.DataFrame, y_train: pd.Series
    ) -> dict[str, Any]:
        """
        超参数优化 (TODO: 实现)

        Args:
            X_train: 训练特征
            y_train: 训练目标

        Returns:
            最佳参数
        """
        logger.info("开始超参数优化")

        # TODO: 实现超参数优化逻辑
        # 可以使用optuna、hyperopt等库

        best_params = {
            "n_estimators": 200,
            "max_depth": 8,
            "learning_rate": 0.05,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
        }

        logger.info("超参数优化完成", best_params=best_params)
        return best_params
