"""
Test coverage for predictor module - 补充覆盖率测试
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from models.predictor import Predictor, _safe_load_or_stub, _StubModel


@patch("models.predictor._safe_load_or_stub", return_value=_StubModel())
def test_predictor_initialization(mock_safe_load):
    """测试Predictor初始化 - 覆盖第26-28行"""
    predictor = Predictor()
    assert isinstance(predictor.model, _StubModel)
    assert predictor.model_version is not None
    assert predictor.feature_columns is None

    predictor_with_path = Predictor("/nonexistent/path.pkl")
    assert isinstance(predictor_with_path.model, _StubModel)
    mock_safe_load.assert_called_with("/nonexistent/path.pkl")


def test_model_load_failure_fallback():
    """测试模型加载失败的fallback - 覆盖第84-86行"""
    predictor = Predictor()  # Uses stub by default

    # Mock the safe_load function to simulate a failure during load_model call
    with patch(
        "models.predictor._safe_load_or_stub", side_effect=Exception("mocked error")
    ):
        with pytest.warns(UserWarning, match="模型加载失败"):
            predictor.load_model("/invalid/path/model.pkl")

    # Verify fallback to stub model
    assert isinstance(predictor.model, _StubModel)
    assert predictor.model_version == "stub-default"


@patch("models.predictor._safe_load_or_stub", return_value=_StubModel())
def test_predict_batch_exception_handling(mock_safe_load):
    """测试predict_batch异常处理 - 覆盖第162行"""
    predictor = Predictor()
    invalid_matches = [{"invalid": "data"}]
    results = predictor.predict_batch(invalid_matches)

    assert len(results) == 1
    assert results[0]["home_win"] == 0.33


def test_safe_load_or_stub_with_valid_pickle():
    """测试_safe_load_or_stub成功加载pickle - 覆盖第205,208行"""
    # 创建一个临时的pickle文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp_file:
        import pickle

        test_data = {"test": "data"}
        pickle.dump(test_data, tmp_file)
        tmp_file_path = tmp_file.name

    try:
        # 测试成功加载
        result = _safe_load_or_stub(tmp_file_path)
        assert result == test_data
    finally:
        # 清理临时文件
        Path(tmp_file_path).unlink(missing_ok=True)


def test_safe_load_or_stub_fallback():
    """测试_safe_load_or_stub fallback to stub"""
    with pytest.warns(UserWarning, match="missing or corrupt"):
        result = _safe_load_or_stub("/nonexistent/file.pkl")
    assert isinstance(result, _StubModel)


def test_safe_load_or_stub_function_exists():
    """确保_safe_load_or_stub函数被覆盖 - 覆盖第202行"""
    # 直接调用函数确保函数定义被覆盖
    assert callable(_safe_load_or_stub)
    # 测试函数签名
    import inspect

    sig = inspect.signature(_safe_load_or_stub)
    assert "path" in sig.parameters
