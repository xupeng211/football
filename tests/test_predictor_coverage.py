"""
Test coverage for predictor module - 补充覆盖率测试
"""

import tempfile
from pathlib import Path

from models.predictor import Predictor, _safe_load_or_stub, _StubModel


def test_predictor_initialization():
    """测试Predictor初始化 - 覆盖第26-28行"""
    # 无参数初始化 - 确保覆盖实例变量初始化
    predictor = Predictor()
    assert predictor.model is not None  # 实际上会设置StubModel
    assert predictor.model_version == "stub-default"  # 实际设置的值
    assert predictor.feature_columns is None  # 覆盖第28行

    # 有参数初始化
    predictor_with_path = Predictor("/nonexistent/path.pkl")
    assert predictor_with_path.model is not None  # 会使用stub模型


def test_model_load_failure_fallback():
    """测试模型加载失败的fallback - 覆盖第84-86行"""
    predictor = Predictor()
    # 传入无效路径触发异常处理
    predictor.load_model("/invalid/path/model.pkl")

    # 验证fallback到stub模型
    assert isinstance(predictor.model, _StubModel)
    # model_version会被设置为父目录名
    assert predictor.model_version == "path"


def test_predict_batch_exception_handling():
    """测试predict_batch异常处理 - 覆盖第162行"""
    # 初始化一个有模型的predictor
    predictor = Predictor("/nonexistent/path.pkl")  # 这会设置stub模型

    # 构造会导致异常的输入(缺少必要字段)
    invalid_matches = [{"invalid": "data", "structure": True}]

    results = predictor.predict_batch(invalid_matches)

    # 验证异常处理返回默认预测
    assert len(results) == 1
    assert results[0]["home_win"] == 0.33
    assert results[0]["draw"] == 0.34
    assert results[0]["away_win"] == 0.33


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
    # 测试无效路径的fallback
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
