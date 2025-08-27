"""
数据摄取抽象基类

定义统一的数据摄取接口,支持从不同来源获取数据
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class DataSource(ABC):
    """数据源抽象基类"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化数据源

        Args:
            config: 数据源配置参数
        """
        self.config = config or {}

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """
        从数据源获取数据

        Returns:
            pd.DataFrame: 获取的数据

        Raises:
            DataSourceError: 数据获取失败时抛出
        """
        pass

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """
        验证数据格式是否正确

        Args:
            df: 待验证的数据

        Returns:
            bool: 验证是否通过
        """
        pass


class DataSourceError(Exception):
    """数据源异常"""

    pass


class MatchDataSource(DataSource):
    """比赛数据源抽象类"""

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """
        获取比赛数据

        Returns:
            pd.DataFrame: 包含以下列的比赛数据
                - id: 比赛ID
                - date: 比赛日期
                - home: 主队ID
                - away: 客队ID
                - home_goals: 主队进球数
                - away_goals: 客队进球数
                - result: 比赛结果 (H/D/A)
        """
        pass

    def validate(self, df: pd.DataFrame) -> bool:
        """验证比赛数据格式"""
        required_columns = ["id", "date", "home", "away", "home_goals", "away_goals", "result"]
        return all(col in df.columns for col in required_columns)


class OddsDataSource(DataSource):
    """赔率数据源抽象类"""

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """
        获取赔率数据

        Returns:
            pd.DataFrame: 包含以下列的赔率数据
                - id: 赔率ID
                - match_id: 比赛ID
                - h: 主胜赔率
                - d: 平局赔率
                - a: 客胜赔率
                - provider: 赔率提供商
        """
        pass

    def validate(self, df: pd.DataFrame) -> bool:
        """验证赔率数据格式"""
        required_columns = ["id", "match_id", "h", "d", "a", "provider"]
        return all(col in df.columns for col in required_columns)
