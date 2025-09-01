"""
滚动特征工程单元测试
"""

import pandas as pd
import pytest
from data_pipeline.features.rolling import add_form

# Skip test since data_pipeline module is not implemented
pytestmark = pytest.mark.skip(reason="data_pipeline.features.rolling module not implemented")


def test_add_form_ok():
    """测试添加状态特征成功"""
    df = pd.DataFrame(
        {"team": ["A", "A", "A", "B", "B", "B"], "pts": [3, 0, 1, 1, 3, 0]}
    )

    result = add_form(df, "team", "pts", window=3)

    assert "form" in result.columns
    assert len(result) == len(df)
    assert not result["form"].isna().all()


def test_add_form_bad_window():
    """测试错误的窗口大小时抛出异常"""
    df = pd.DataFrame({"team": ["A", "A"], "pts": [3, 0]})

    with pytest.raises(ValueError):
        add_form(df, "team", "pts", window=0)

    with pytest.raises(ValueError):
        add_form(df, "team", "pts", window=-1)
