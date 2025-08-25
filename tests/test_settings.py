"""
配置设置测试 - 测试应用配置和设置
"""

import pytest


def test_settings_import():
    """测试设置模块导入"""
    from apps.api.core.settings import Settings, settings

    assert Settings is not None
    assert settings is not None


def test_settings_attributes():
    """测试设置属性"""
    from apps.api.core.settings import settings

    # 测试基本属性存在
    assert hasattr(settings, "app_port")
    assert hasattr(settings, "database_url")
    assert hasattr(settings, "log_level")
    assert hasattr(settings, "model_version")

    # 测试默认值
    assert isinstance(settings.app_port, int)
    assert isinstance(settings.database_url, str)
    assert isinstance(settings.log_level, str)


def test_settings_defaults():
    """测试设置默认值"""
    from apps.api.core.settings import Settings

    # 创建新的设置实例测试默认值
    test_settings = Settings()

    assert test_settings.app_port == 8000
    assert test_settings.log_level == "INFO"
    assert test_settings.model_version == "latest"


def test_logging_setup():
    """测试日志设置"""
    try:
        from apps.api.core.logging import setup_logging

        # 测试日志设置函数可以调用
        setup_logging()

    except ImportError:
        pytest.skip("日志模块不可用")
