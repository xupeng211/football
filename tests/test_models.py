"""
模型相关测试 - 测试模型注册表和基本功能
"""

from unittest.mock import MagicMock, mock_open, patch

import pytest


def test_model_registry_import():
    """测试模型注册表导入"""
    from models.registry import ModelRegistry

    assert ModelRegistry is not None


def test_model_registry_basic():
    """测试模型注册表基本功能"""
    from models.registry import ModelRegistry

    # 使用临时路径避免文件系统副作用
    with (
        patch("models.registry.Path") as mock_path,
        patch("builtins.open", new_callable=mock_open, read_data="{}"),
    ):
        mock_path.return_value.mkdir = MagicMock()
        mock_path.return_value.exists.return_value = True

        registry = ModelRegistry(registry_path="/tmp/test_registry")
        assert registry is not None


def test_load_model_function():
    """测试模型加载函数"""
    pytest.skip("load_model函数不在当前registry模块中")


def test_dummy_model():
    """测试占位模型"""
    pytest.skip("load_model函数不在当前registry模块中")
