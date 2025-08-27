"""
滚动统计特征工程

实现基于时间序列的滚动统计特征计算
"""

import pandas as pd


def add_form(
    df: pd.DataFrame, team_col: str, points_col: str, window: int = 5, min_periods: int = 1
) -> pd.DataFrame:
    """
    计算球队状态（滚动积分平均）

    Args:
        df: 输入数据框，需包含球队和积分列
        team_col: 球队列名
        points_col: 积分列名
        window: 滚动窗口大小
        min_periods: 最少需要的周期数

    Returns:
        pd.DataFrame: 添加了'form'列的数据框

    Raises:
        ValueError: 当window <= 0时抛出
    """
    if window <= 0:
        raise ValueError("滚动窗口大小必须大于0")

    df = df.copy()

    # 按球队分组计算滚动平均
    df["form"] = (
        df.groupby(team_col)[points_col]
        .rolling(window=window, min_periods=min_periods)
        .mean()
        .reset_index(level=0, drop=True)
    )

    return df


def add_goal_diff(
    df: pd.DataFrame, team_col: str, goals_for_col: str, goals_against_col: str, window: int = 5
) -> pd.DataFrame:
    """
    计算滚动净胜球

    Args:
        df: 输入数据框
        team_col: 球队列名
        goals_for_col: 进球列名
        goals_against_col: 失球列名
        window: 滚动窗口大小

    Returns:
        pd.DataFrame: 添加了'goal_diff'列的数据框
    """
    if window <= 0:
        raise ValueError("滚动窗口大小必须大于0")

    df = df.copy()

    # 计算净胜球
    df["temp_goal_diff"] = df[goals_for_col] - df[goals_against_col]

    # 按球队分组计算滚动平均净胜球
    df["goal_diff"] = (
        df.groupby(team_col)["temp_goal_diff"]
        .rolling(window=window, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )

    # 删除临时列
    df = df.drop("temp_goal_diff", axis=1)

    return df


def add_rolling_stats(
    df: pd.DataFrame,
    team_col: str,
    value_col: str,
    window: int = 5,
    stats: list[str] | None = None,
    prefix: str = "",
) -> pd.DataFrame:
    """
    通用滚动统计函数

    Args:
        df: 输入数据框
        team_col: 球队列名
        value_col: 数值列名
        window: 滚动窗口大小
        stats: 统计函数列表，默认['mean', 'std']
        prefix: 新列名前缀

    Returns:
        pd.DataFrame: 添加了滚动统计列的数据框
    """
    if stats is None:
        stats = ["mean", "std"]

    if window <= 0:
        raise ValueError("滚动窗口大小必须大于0")

    df = df.copy()

    for stat in stats:
        col_name = (
            f"{prefix}{value_col}_{stat}_{window}" if prefix else f"{value_col}_{stat}_{window}"
        )

        if stat == "mean":
            df[col_name] = (
                df.groupby(team_col)[value_col]
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(level=0, drop=True)
            )
        elif stat == "std":
            df[col_name] = (
                df.groupby(team_col)[value_col]
                .rolling(window=window, min_periods=2)
                .std()
                .reset_index(level=0, drop=True)
            )
        elif stat == "sum":
            df[col_name] = (
                df.groupby(team_col)[value_col]
                .rolling(window=window, min_periods=1)
                .sum()
                .reset_index(level=0, drop=True)
            )
        elif stat == "max":
            df[col_name] = (
                df.groupby(team_col)[value_col]
                .rolling(window=window, min_periods=1)
                .max()
                .reset_index(level=0, drop=True)
            )
        elif stat == "min":
            df[col_name] = (
                df.groupby(team_col)[value_col]
                .rolling(window=window, min_periods=1)
                .min()
                .reset_index(level=0, drop=True)
            )
        else:
            raise ValueError(f"不支持的统计函数: {stat}")

    return df


def calculate_points(result: str, is_home: bool) -> int:
    """
    根据比赛结果计算积分

    Args:
        result: 比赛结果 'H'/'D'/'A'
        is_home: 是否为主队

    Returns:
        int: 积分 (3胜/1平/0负)
    """
    if result == "D":  # 平局
        return 1
    elif (result == "H" and is_home) or (result == "A" and not is_home):
        return 3  # 胜利
    else:
        return 0  # 失败


def add_recent_form(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    为比赛数据添加主客队近期状态

    Args:
        df: 比赛数据框，需包含 'home', 'away', 'result' 列
        window: 状态计算窗口

    Returns:
        pd.DataFrame: 添加了 'home_form', 'away_form' 列的数据框
    """
    df = df.copy()

    # 创建主队数据
    home_data = df[["home", "result"]].copy()
    home_data["team"] = home_data["home"]
    home_data["points"] = home_data["result"].apply(lambda x: calculate_points(x, is_home=True))

    # 创建客队数据
    away_data = df[["away", "result"]].copy()
    away_data["team"] = away_data["away"]
    away_data["points"] = away_data["result"].apply(lambda x: calculate_points(x, is_home=False))

    # 合并所有球队数据
    all_team_data = pd.concat(
        [home_data[["team", "points"]], away_data[["team", "points"]]]
    ).reset_index()

    # 计算滚动状态
    all_team_data = add_form(all_team_data, "team", "points", window)

    # 将状态合并回原数据
    # 为主队添加状态
    home_form_data = all_team_data[all_team_data["team"].isin(df["home"])]
    home_form_map = dict(zip(home_form_data.index, home_form_data["form"], strict=False))
    df["home_form"] = df.index.map(home_form_map)

    # 为客队添加状态
    away_form_data = all_team_data[all_team_data["team"].isin(df["away"])]
    away_form_map = dict(zip(away_form_data.index, away_form_data["form"], strict=False))
    df["away_form"] = df.index.map(away_form_map)

    # 填充缺失值
    df["home_form"] = df["home_form"].fillna(1.5)  # 默认状态
    df["away_form"] = df["away_form"].fillna(1.5)  # 默认状态

    return df
