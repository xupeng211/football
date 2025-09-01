"""
基础测试 - 验证项目结构和模块导入
"""

import sys
from pathlib import Path

import pytest


def test_project_structure():
    """测试项目目录结构"""
    root = Path(".")
    assert root.exists(), "The project root directory does not exist."

    # 检查核心模块
    core_modules = ["apps", "data_pipeline", "models", "trainer", "infra", "evaluation"]
    for module in core_modules:
        module_path = root / module
        assert module_path.exists(), f"模块目录 {module} 不存在"

    # Check other important top-level directories
    other_dirs = ["docs", "prompts", "tests"]
    for dir_name in other_dirs:
        assert (Path(".") / dir_name).exists(), f"目录 {dir_name} 不存在"


def test_config_files():
    """测试配置文件存在性"""
    root = Path(".")

    config_files = [
        "pyproject.toml",
        ".env.example",
        "Makefile",
        "README.md",
    ]

    for config_file in config_files:
        assert (root / config_file).exists(), f"配置文件 {config_file} 不存在"


def test_docs_structure():
    """测试文档结构"""
    docs_dir = Path("docs")
    assert docs_dir.exists(), "docs目录不存在"

    # 检查重要文档文件
    important_docs = ["TASKS.md", "dev_log.md"]
    for doc in important_docs:
        assert (docs_dir / doc).exists(), f"文档 {doc} 不存在"


def test_api_module_import():
    """测试API模块导入"""
    try:
        # 测试核心模块导入
        from football_predict_system.core.config import get_settings

        settings = get_settings()

        # 验证配置可以获取
        assert hasattr(settings, "api")
        assert hasattr(settings.api, "port")
        assert hasattr(settings, "database")
        assert hasattr(settings.database, "url")

    except ImportError as e:
        pytest.fail(f"API模块导入失败: {e}")


@pytest.mark.skip(reason="data_pipeline模块尚未实现")
def test_data_pipeline_import():
    """测试数据管道模块导入"""
    # TODO: 实现data_pipeline模块
    pass


@pytest.mark.skip(reason="XGBoostTrainer模块尚未实现")
def test_trainer_import():
    """测试训练器模块导入"""
    try:
        from apps.trainer.xgboost_trainer import XGBoostTrainer

        # 验证类可以实例化
        # A mock config is needed for instantiation
        class MockConfig:
            n_estimators = 100
            learning_rate = 0.1
            max_depth = 3
            objective = "binary:logistic"
            eval_metric = "logloss"
            seed = 42
            num_class = 3
            random_state = 42

        trainer = XGBoostTrainer(config=MockConfig())
        assert trainer is not None

    except ImportError as e:
        pytest.fail(f"训练器模块导入失败: {e}")


def test_models_import():
    """测试模型注册表模块导入"""
    try:
        from models.registry import ModelRegistry

        # 验证类可以实例化
        registry = ModelRegistry()
        assert registry is not None

    except ImportError as e:
        pytest.fail(f"模型注册表模块导入失败: {e}")


@pytest.mark.skip(reason="BacktestEngine模块尚未实现")
def test_backtest_import():
    """测试回测模块导入"""
    try:
        from apps.backtest.engine import BacktestEngine

        # 验证类可以实例化
        engine = BacktestEngine()
        assert engine is not None

    except ImportError as e:
        pytest.fail(f"回测模块导入失败: {e}")


def test_python_version():
    """测试Python版本"""
    version_info = sys.version_info
    assert version_info >= (3, 11), f"需要Python 3.11+, 当前版本: {version_info}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
