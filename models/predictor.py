"""
足球比赛结果预测器

加载训练好的模型并提供预测接口
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from data_pipeline.features.build import create_feature_vector


class Predictor:
    """足球比赛结果预测器"""

    def __init__(self, model_path: str | None = None):
        """
        初始化预测器

        Args:
            model_path: 模型文件路径,如果为None则加载最新模型
        """
        self.model: Any = None
        self.model_version: str | None = None
        self.feature_columns: list[str] | None = None

        # 立即加载模型
        if model_path:
            self.model = _safe_load_or_stub(model_path)
            self.model_version = (
                model_path.split("/")[-1] if "/" in model_path else model_path
            )
        else:
            # 尝试加载最新模型,失败则使用stub
            latest_model_path = self._find_latest_model()
            if latest_model_path:
                self.model = _safe_load_or_stub(latest_model_path)
                self.model_version = (
                    latest_model_path.split("/")[-1]
                    if "/" in latest_model_path
                    else "latest"
                )
            else:
                self.model = _safe_load_or_stub(None)  # 这会返回StubModel
                self.model_version = "stub-default"

    def _find_latest_model(self) -> str | None:
        """查找最新的模型文件"""
        models_dir = Path("models")
        if not models_dir.exists():
            return None

        # 查找所有模型目录
        model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
        if not model_dirs:
            return None

        # 按创建时间排序,选择最新的
        latest_dir = max(model_dirs, key=lambda x: x.stat().st_ctime)

        model_file = latest_dir / "model.pkl"
        if model_file.exists():
            return str(model_file)

        return None

    def load_model(self, model_path: str) -> None:
        """
        加载模型

        Args:
            model_path: 模型文件路径
        """
        try:
            self.model = _safe_load_or_stub(model_path)

            # 获取模型版本信息
            model_dir = Path(model_path).parent
            self.model_version = model_dir.name

            # 尝试加载特征列信息
            metrics_file = model_dir / "metrics.json"
            if metrics_file.exists():
                with open(metrics_file, encoding="utf-8") as f:
                    metrics = json.load(f)
                    if "feature_importance" in metrics:
                        self.feature_columns = list(
                            metrics["feature_importance"].keys()
                        )

            print(f"模型加载成功: {self.model_version}")

        except Exception as e:
            # 如果加载失败,使用stub模型
            import warnings

            warnings.warn(f"模型加载失败,使用默认模型: {e}", stacklevel=2)
            self.model = _StubModel()
            self.model_version = "stub-default"

    def predict_single(
        self,
        home_team: str,
        away_team: str,
        odds_h: float,
        odds_d: float,
        odds_a: float,
    ) -> dict[str, Any]:
        """
        预测单场比赛结果

        Args:
            home_team: 主队名称
            away_team: 客队名称
            odds_h: 主胜赔率
            odds_d: 平局赔率
            odds_a: 客胜赔率

        Returns:
            Dict[str, float]: 预测结果

        Raises:
            RuntimeError: 当模型未加载时
            ValueError: 当输入参数无效时
        """
        if self.model is None:
            raise RuntimeError("模型未加载")

        try:
            # 创建特征向量(包含输入验证)
            features = create_feature_vector(
                home_team=home_team,
                away_team=away_team,
                odds_h=odds_h,
                odds_d=odds_d,
                odds_a=odds_a,
            )
        except ValueError as e:
            # 重新抛出验证错误,提供更好的错误信息
            raise ValueError(f"输入验证失败: {e}") from e
        except Exception as e:
            # 捕获其他意外错误
            raise RuntimeError(f"特征生成失败: {e}") from e

        # 转换为DataFrame
        feature_df = pd.DataFrame([features])

        # 如果有特征列信息,确保列顺序一致
        if self.feature_columns:
            missing_cols = set(self.feature_columns) - set(feature_df.columns)
            for col in missing_cols:
                feature_df[col] = 0.0  # 填充缺失特征
            feature_df = feature_df[self.feature_columns]

        try:
            # 预测
            proba = self.model.predict_proba(feature_df)[0]
        except Exception as e:
            raise RuntimeError(f"模型预测失败: {e}") from e

        # 确定预测结果
        prob_home = float(proba[0])
        prob_draw = float(proba[1])
        prob_away = float(proba[2])

        # 找出最大概率对应的结果
        max_prob = max(prob_home, prob_draw, prob_away)
        if max_prob == prob_home:
            predicted_outcome = "home_win"
            confidence = prob_home
        elif max_prob == prob_draw:
            predicted_outcome = "draw"
            confidence = prob_draw
        else:
            predicted_outcome = "away_win"
            confidence = prob_away

        return {
            "home_win": prob_home,
            "draw": prob_draw,
            "away_win": prob_away,
            "predicted_outcome": predicted_outcome,
            "confidence": confidence,
            "model_version": self.model_version or "unknown",
        }

    def predict_batch(self, matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        批量预测比赛结果

        Args:
            matches: 比赛列表,每个元素包含 home, away, odds_h, odds_d, odds_a 等字段

        Returns:
            List[Dict[str, float]]: 预测结果列表
        """
        if self.model is None:
            raise RuntimeError("模型未加载")

        results = []
        for match in matches:
            try:
                result = self.predict_single(
                    home_team=match.get("home", ""),
                    away_team=match.get("away", ""),
                    odds_h=match.get("odds_h", match.get("h", 2.0)),
                    odds_d=match.get("odds_d", match.get("d", 3.0)),
                    odds_a=match.get("odds_a", match.get("a", 3.0)),
                )
                results.append(result)
            except Exception:
                # 返回默认预测(平均分布)
                results.append(
                    {
                        "home_win": 0.33,
                        "draw": 0.34,
                        "away_win": 0.33,
                        "predicted_outcome": "draw",
                        "confidence": 0.34,
                        "model_version": self.model_version or "unknown",
                    }
                )

        return results

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        if self.model is None:
            return {"status": "no_model_loaded"}

        info = {
            "model_version": self.model_version,
            "model_type": type(self.model).__name__,
            "is_loaded": True,
        }

        return info


def create_predictor(model_path: str | None = None) -> Predictor:
    """创建预测器实例"""
    return Predictor(model_path)


# --- Fallback: stub when no model present ---
class _StubModel:
    def predict_proba(self, X: pd.DataFrame) -> Any:
        import numpy as np

        return np.array([[0.34, 0.33, 0.33] for _ in range(len(X))])

    def predict(self, X: pd.DataFrame) -> Any:
        import numpy as np

        proba = self.predict_proba(X)
        return np.argmax(proba, axis=1)


def _safe_load_or_stub(path: str | None) -> Any:
    """安全加载模型,失败时返回stub"""
    if path is None:
        import warnings

        warnings.warn("Predictor: model path is None, using stub", stacklevel=2)
        return _StubModel()
    try:
        import pickle  # nosec B403

        with open(path, "rb") as f:
            return pickle.load(f)  # nosec B301
    except Exception:
        import warnings

        warnings.warn(
            f"Predictor: model at {path} missing or corrupt, using stub",
            stacklevel=2,
        )
        return _StubModel()
