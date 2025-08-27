"""
CSV数据摄取单元测试
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from data_pipeline.ingest.base import DataSourceError
from data_pipeline.ingest.csv_adapter import (
    CSVMatchDataSource,
    CSVOddsDataSource,
    get_sample_data_path,
)


class TestCSVMatchDataSource:
    """CSV比赛数据源测试"""

    def test_fetch_sample_data_ok(self):
        """测试读取样例比赛数据成功"""
        source = CSVMatchDataSource(get_sample_data_path("matches.csv"))
        df = source.fetch()

        # 验证数据结构
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        required_cols = ["id", "date", "home", "away", "home_goals", "away_goals", "result"]
        assert all(col in df.columns for col in required_cols)

        # 验证数据类型
        assert df["date"].dtype.name.startswith("datetime")
        assert df["home"].dtype == "int64"
        assert df["away"].dtype == "int64"

        # 验证数据内容
        assert len(df) > 0
        assert df["result"].isin(["H", "D", "A"]).all()

    def test_fetch_nonexistent_file(self):
        """测试读取不存在的文件时抛出异常"""
        source = CSVMatchDataSource("/path/to/nonexistent/file.csv")

        with pytest.raises(DataSourceError) as exc_info:
            source.fetch()

        assert "CSV文件不存在" in str(exc_info.value)

    def test_fetch_empty_file(self):
        """测试读取空文件时抛出异常"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # 创建空文件
            temp_path = f.name

        try:
            source = CSVMatchDataSource(temp_path)
            with pytest.raises(DataSourceError) as exc_info:
                source.fetch()

            assert "CSV文件为空" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_fetch_invalid_format(self):
        """测试读取格式错误的文件时抛出异常"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # 写入格式错误的CSV
            f.write("wrong,columns,format\n1,2,3\n")
            temp_path = f.name

        try:
            source = CSVMatchDataSource(temp_path)
            with pytest.raises(DataSourceError) as exc_info:
                source.fetch()

            assert "CSV文件格式不正确" in str(exc_info.value)
        finally:
            os.unlink(temp_path)


class TestCSVOddsDataSource:
    """CSV赔率数据源测试"""

    def test_fetch_sample_data_ok(self):
        """测试读取样例赔率数据成功"""
        source = CSVOddsDataSource(get_sample_data_path("odds.csv"))
        df = source.fetch()

        # 验证数据结构
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        required_cols = ["id", "match_id", "h", "d", "a", "provider"]
        assert all(col in df.columns for col in required_cols)

        # 验证数据类型
        assert df["match_id"].dtype == "int64"
        assert df["h"].dtype == "float64"
        assert df["d"].dtype == "float64"
        assert df["a"].dtype == "float64"

        # 验证赔率为正数
        assert (df["h"] > 0).all()
        assert (df["d"] > 0).all()
        assert (df["a"] > 0).all()

    def test_fetch_nonexistent_file(self):
        """测试读取不存在的文件时抛出异常"""
        source = CSVOddsDataSource("/path/to/nonexistent/odds.csv")

        with pytest.raises(DataSourceError) as exc_info:
            source.fetch()

        assert "CSV文件不存在" in str(exc_info.value)

    def test_fetch_negative_odds(self):
        """测试读取包含负赔率的文件时抛出异常"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # 写入包含负赔率的CSV
            f.write("id,match_id,h,d,a,provider\n1,1,-1.5,3.0,2.0,test\n")
            temp_path = f.name

        try:
            source = CSVOddsDataSource(temp_path)
            with pytest.raises(DataSourceError) as exc_info:
                source.fetch()

            assert "赔率必须为正数" in str(exc_info.value)
        finally:
            os.unlink(temp_path)


def test_get_sample_data_path():
    """测试获取样例数据路径"""
    path = get_sample_data_path("matches.csv")
    assert isinstance(path, str)
    assert path.endswith("sql/sample/matches.csv")
    assert Path(path).name == "matches.csv"
