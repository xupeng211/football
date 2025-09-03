"""
配置测试 - 验证系统配置功能
"""

import pytest


def test_settings_import():
    """测试设置模块导入"""
    try:
        from football_predict_system.core.config import Settings, get_settings

        # 验证函数可以调用
        settings = get_settings()
        assert settings is not None
        assert isinstance(settings, Settings)

    except ImportError as e:
        pytest.fail(f"设置模块导入失败: {e}")


def test_settings_attributes():
    """测试设置属性"""
    try:
        from football_predict_system.core.config import get_settings

        settings = get_settings()

        # 验证必要的配置属性存在
        assert hasattr(settings, "api")
        assert hasattr(settings, "database")
        assert hasattr(settings.api, "port")
        assert hasattr(settings.database, "url")

    except ImportError as e:
        pytest.fail(f"设置属性测试失败: {e}")


def test_settings_defaults():
    """测试设置默认值"""
    try:
        from football_predict_system.core.config import Settings

        # 创建默认设置实例
        settings = Settings()
        assert settings is not None

        # 验证默认端口
        assert settings.api.port == 8000

    except ImportError as e:
        pytest.fail(f"设置默认值测试失败: {e}")


@pytest.mark.skip(reason="日志模块不可用")
def test_logging_setup():
    """测试日志设置"""
    # TODO: 实现日志配置测试
