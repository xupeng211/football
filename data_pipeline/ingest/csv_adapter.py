"""
CSV数据源适配器

实现从CSV文件读取比赛和赔率数据
"""

from pathlib import Path
from typing import Any

import pandas as pd

from .base import DataSourceError, MatchDataSource, OddsDataSource


class CSVMatchDataSource(MatchDataSource):
    """CSV比赛数据源"""

    def __init__(self, file_path: str, config: dict[str, Any] | None = None):
        """
        初始化CSV比赛数据源

        Args:
            file_path: CSV文件路径
            config: 配置参数
        """
        super().__init__(config)
        self.file_path = Path(file_path)

    def fetch(self) -> pd.DataFrame:
        """
        从CSV文件读取比赛数据

        Returns:
            pd.DataFrame: 比赛数据

        Raises:
            DataSourceError: 文件不存在或读取失败时抛出
        """
        try:
            if not self.file_path.exists():
                raise DataSourceError(f"CSV文件不存在: {self.file_path}")

            df = pd.read_csv(self.file_path)

            if df.empty:
                raise DataSourceError(f"CSV文件为空: {self.file_path}")

            if not self.validate(df):
                raise DataSourceError(f"CSV文件格式不正确: {self.file_path}")

            # 转换数据类型
            df["date"] = pd.to_datetime(df["date"])
            df["home"] = df["home"].astype(int)
            df["away"] = df["away"].astype(int)
            df["home_goals"] = df["home_goals"].astype("Int64")  # 允许NULL
            df["away_goals"] = df["away_goals"].astype("Int64")  # 允许NULL

            return df

        except pd.errors.EmptyDataError as e:
            raise DataSourceError(f"CSV文件为空: {self.file_path}") from e
        except pd.errors.ParserError as e:
            raise DataSourceError(
                f"CSV文件解析失败: {self.file_path}, 错误: {e}"
            ) from e
        except Exception as e:
            raise DataSourceError(
                f"读取CSV文件失败: {self.file_path}, 错误: {e}"
            ) from e


class CSVOddsDataSource(OddsDataSource):
    """CSV赔率数据源"""

    def __init__(self, file_path: str, config: dict[str, Any] | None = None):
        """
        初始化CSV赔率数据源

        Args:
            file_path: CSV文件路径
            config: 配置参数
        """
        super().__init__(config)
        self.file_path = Path(file_path)

    def fetch(self) -> pd.DataFrame:
        """
        从CSV文件读取赔率数据

        Returns:
            pd.DataFrame: 赔率数据

        Raises:
            DataSourceError: 文件不存在或读取失败时抛出
        """
        try:
            if not self.file_path.exists():
                raise DataSourceError(f"CSV文件不存在: {self.file_path}")

            df = pd.read_csv(self.file_path)

            if df.empty:
                raise DataSourceError(f"CSV文件为空: {self.file_path}")

            if not self.validate(df):
                raise DataSourceError(f"CSV文件格式不正确: {self.file_path}")

            # 转换数据类型
            df["match_id"] = df["match_id"].astype(int)
            df["h"] = df["h"].astype(float)
            df["d"] = df["d"].astype(float)
            df["a"] = df["a"].astype(float)

            # 验证赔率合理性
            if (df["h"] <= 0).any() or (df["d"] <= 0).any() or (df["a"] <= 0).any():
                raise DataSourceError("赔率必须为正数")

            return df

        except pd.errors.EmptyDataError as e:
            raise DataSourceError(f"CSV文件为空: {self.file_path}") from e
        except pd.errors.ParserError as e:
            raise DataSourceError(
                f"CSV文件解析失败: {self.file_path}, 错误: {e}"
            ) from e
        except Exception as e:
            raise DataSourceError(
                f"读取CSV文件失败: {self.file_path}, 错误: {e}"
            ) from e


def get_sample_data_path(filename: str) -> str:
    """
    获取样例数据文件路径

    Args:
        filename: 文件名 (如 'matches.csv', 'odds.csv')

    Returns:
        str: 完整文件路径
    """
    # 从当前文件位置找到项目根目录
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent  # 上两级目录
    sample_dir = project_root / "sql" / "sample"
    return str(sample_dir / filename)


def create_sample_match_source() -> CSVMatchDataSource:
    """创建样例比赛数据源"""
    file_path = get_sample_data_path("matches.csv")
    return CSVMatchDataSource(file_path)


def create_sample_odds_source() -> CSVOddsDataSource:
    """创建样例赔率数据源"""
    file_path = get_sample_data_path("odds.csv")
    return CSVOddsDataSource(file_path)
