"""
特征构建模块

将原始比赛和赔率数据转换为机器学习特征
"""

from typing import Any

import numpy as np
import pandas as pd

from .rolling import add_recent_form, add_rolling_stats


def build_match_features(
    matches_df: pd.DataFrame,
    odds_df: pd.DataFrame,
    feature_config: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    构建比赛特征

    Args:
        matches_df: 比赛数据
        odds_df: 赔率数据
        feature_config: 特征配置参数

    Returns:
        pd.DataFrame: 特征数据框
    """
    if feature_config is None:
        feature_config = get_default_feature_config()

    # 确保数据按日期排序
    matches_df = matches_df.sort_values("date").reset_index(drop=True)

    # 合并赔率数据
    df = matches_df.merge(odds_df, left_on="id", right_on="match_id", how="left")

    # 添加基础特征
    df = add_basic_features(df)

    # 添加状态特征
    df = add_form_features(df, feature_config)

    # 添加赔率特征
    df = add_odds_features(df)

    # 添加历史对战特征
    df = add_head_to_head_features(df, feature_config)

    # 清理和标准化
    df = clean_features(df)

    return df


def get_default_feature_config() -> dict[str, Any]:
    """获取默认特征配置"""
    return {
        "form_window": 5,
        "goal_window": 5,
        "h2h_window": 10,
        "min_matches": 3,
        "fill_na_strategy": "mean",
    }


def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    """添加基础特征"""
    df = df.copy()

    # 主客场标识
    df["is_home"] = 1
    df["is_away"] = 0

    # 比赛结果编码
    df["target"] = df["result"].map({"H": 0, "D": 1, "A": 2})

    # 进球相关特征
    df["total_goals"] = df["home_goals"] + df["away_goals"]
    df["goal_difference"] = df["home_goals"] - df["away_goals"]
    df["both_teams_scored"] = ((df["home_goals"] > 0) & (df["away_goals"] > 0)).astype(
        int
    )

    # 比赛强度特征
    df["high_scoring"] = (df["total_goals"] > 2.5).astype(int)
    df["low_scoring"] = (df["total_goals"] < 1.5).astype(int)

    return df


def add_form_features(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """添加状态特征"""
    df = df.copy()

    # 计算近期状态
    df = add_recent_form(df, window=config["form_window"])

    # 计算进球状态
    home_goals_data = df[["home", "home_goals", "away_goals"]].copy()
    home_goals_data.columns = ["team", "goals_for", "goals_against"]

    away_goals_data = df[["away", "away_goals", "home_goals"]].copy()
    away_goals_data.columns = ["team", "goals_for", "goals_against"]

    # 合并进球数据
    all_goals_data = pd.concat([home_goals_data, away_goals_data])
    all_goals_data = all_goals_data.reset_index()

    # 计算滚动进球统计
    all_goals_data = add_rolling_stats(
        all_goals_data,
        "team",
        "goals_for",
        window=config["goal_window"],
        stats=["mean"],
        prefix="avg_",
    )

    all_goals_data = add_rolling_stats(
        all_goals_data,
        "team",
        "goals_against",
        window=config["goal_window"],
        stats=["mean"],
        prefix="avg_",
    )

    # 将进球统计合并回原数据
    # 这里简化处理,实际应该基于时间窗口
    team_stats = (
        all_goals_data.groupby("team")
        .agg(
            {
                "avg_goals_for_mean_5": "last",
                "avg_goals_against_mean_5": "last",
            }
        )
        .reset_index()
    )

    # 为主队添加统计
    df = df.merge(
        team_stats,
        left_on="home",
        right_on="team",
        how="left",
        suffixes=("", "_home"),
    )
    df = df.rename(
        columns={
            "avg_goals_for_mean_5": "home_avg_goals_for",
            "avg_goals_against_mean_5": "home_avg_goals_against",
        }
    )
    df = df.drop("team", axis=1)

    # 为客队添加统计
    df = df.merge(
        team_stats,
        left_on="away",
        right_on="team",
        how="left",
        suffixes=("", "_away"),
    )
    df = df.rename(
        columns={
            "avg_goals_for_mean_5": "away_avg_goals_for",
            "avg_goals_against_mean_5": "away_avg_goals_against",
        }
    )
    df = df.drop("team", axis=1)

    return df


def add_odds_features(df: pd.DataFrame) -> pd.DataFrame:
    """添加赔率特征"""
    df = df.copy()

    # 隐含概率
    df["prob_h"] = 1 / df["h"]
    df["prob_d"] = 1 / df["d"]
    df["prob_a"] = 1 / df["a"]

    # 标准化概率(去除赔率商利润)
    total_prob = df["prob_h"] + df["prob_d"] + df["prob_a"]
    df["prob_h_norm"] = df["prob_h"] / total_prob
    df["prob_d_norm"] = df["prob_d"] / total_prob
    df["prob_a_norm"] = df["prob_a"] / total_prob

    # 赔率差异特征
    df["odds_spread"] = df["h"].max() - df["h"].min()  # 简化版本
    df["favorite"] = np.where(df["h"] < df["a"], "home", "away")
    df["favorite_odds"] = np.minimum(df["h"], df["a"])
    df["underdog_odds"] = np.maximum(df["h"], df["a"])

    # 市场信心度
    df["market_confidence"] = 1 / df["favorite_odds"]

    return df


def add_head_to_head_features(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """添加历史对战特征"""
    df = df.copy()

    # 简化版本:计算基础对战统计
    # 实际实现需要基于历史数据的时间窗口

    # 为每场比赛添加对战记录特征
    df["h2h_home_wins"] = 0  # 占位符
    df["h2h_draws"] = 0  # 占位符
    df["h2h_away_wins"] = 0  # 占位符
    df["h2h_total_matches"] = 0  # 占位符

    # 如果有足够的历史数据,这里应该实现真实的对战统计
    # 由于这是MVP版本,先用占位符

    return df


def clean_features(df: pd.DataFrame) -> pd.DataFrame:
    """清理和标准化特征"""
    df = df.copy()

    # 填充缺失值
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        if col not in ["id", "home", "away", "target"]:
            mean_val = df[col].mean()
            if pd.isna(mean_val):
                mean_val = 0  # 如果无法计算平均值, 则默认为0
            df[col] = df[col].fillna(mean_val)

    # 移除不需要的列
    columns_to_drop = ["date", "result", "provider", "match_id"]
    df = df.drop([col for col in columns_to_drop if col in df.columns], axis=1)

    return df


def create_feature_vector(
    home_team: str,
    away_team: str,
    odds_h: float,
    odds_d: float,
    odds_a: float,
    team_stats: dict | None = None,
) -> dict[str, float]:
    """
    为单场比赛创建特征向量(用于预测)

    Args:
        home_team: 主队名称
        away_team: 客队名称
        odds_h: 主胜赔率
        odds_d: 平局赔率
        odds_a: 客胜赔率
        team_stats: 球队统计数据

    Returns:
        Dict[str, float]: 特征字典
    """

    # 输入验证和安全检查
    def validate_team_name(name: str, field_name: str) -> str:
        if not isinstance(name, str):
            msg = f"{field_name}必须是字符串类型"
            raise ValueError(msg)
        if len(name) > 100:  # 防止DoS攻击
            raise ValueError(f"{field_name}长度不能超过100个字符")
        if not name.strip():
            raise ValueError(f"{field_name}不能为空")
        return name.strip()

    def validate_odds(value: float, field_name: str) -> float:
        # 类型检查
        if not isinstance(value, (int, float)):
            msg = f"{field_name}必须是数字类型,收到:{type(value)}"
            raise ValueError(msg)

        # 转换为float
        try:
            odds_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name}无法转换为数字:{value}")

        # 数值有效性检查
        import math

        if math.isnan(odds_value):
            raise ValueError(f"{field_name}不能是NaN")
        if math.isinf(odds_value):
            raise ValueError(f"{field_name}不能是无穷大")
        if odds_value <= 0:
            raise ValueError(f"{field_name}必须大于0,收到:{odds_value}")
        if odds_value > 1000:  # 合理的上限
            msg = f"{field_name}过大,最大值1000,收到:{odds_value}"
            raise ValueError(msg)

        return odds_value

    # 验证输入
    home_team = validate_team_name(home_team, "主队名称")
    away_team = validate_team_name(away_team, "客队名称")
    odds_h = validate_odds(odds_h, "主胜赔率")
    odds_d = validate_odds(odds_d, "平局赔率")
    odds_a = validate_odds(odds_a, "客胜赔率")

    features = {}

    # 基础赔率特征
    features["h"] = odds_h
    features["d"] = odds_d
    features["a"] = odds_a

    # 隐含概率 - 现在安全了,因为已经验证了输入
    features["prob_h"] = 1 / odds_h
    features["prob_d"] = 1 / odds_d
    features["prob_a"] = 1 / odds_a

    # 标准化概率
    total_prob = features["prob_h"] + features["prob_d"] + features["prob_a"]
    features["prob_h_norm"] = features["prob_h"] / total_prob
    features["prob_d_norm"] = features["prob_d"] / total_prob
    features["prob_a_norm"] = features["prob_a"] / total_prob

    # 主客场标识
    features["is_home"] = 1
    features["is_away"] = 0

    # 如果有球队统计数据,添加相关特征
    if team_stats:
        features["home_form"] = team_stats.get("home_form", 1.5)
        features["away_form"] = team_stats.get("away_form", 1.5)
        features["home_avg_goals_for"] = team_stats.get("home_avg_goals_for", 1.5)
        features["home_avg_goals_against"] = team_stats.get(
            "home_avg_goals_against", 1.5
        )
        features["away_avg_goals_for"] = team_stats.get("away_avg_goals_for", 1.5)
        features["away_avg_goals_against"] = team_stats.get(
            "away_avg_goals_against", 1.5
        )
    else:
        # 使用默认值
        features["home_form"] = 1.5
        features["away_form"] = 1.5
        features["home_avg_goals_for"] = 1.5
        features["home_avg_goals_against"] = 1.5
        features["away_avg_goals_for"] = 1.5
        features["away_avg_goals_against"] = 1.5

    # 市场相关特征
    features["favorite_odds"] = min(odds_h, odds_a)
    features["underdog_odds"] = max(odds_h, odds_a)
    features["market_confidence"] = 1 / features["favorite_odds"]

    return features
