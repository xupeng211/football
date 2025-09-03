"""
配置测试 - 验证系统配置功能
"""

from football_predict_system.core.config import Settings, get_settings
from football_predict_system.core.constants import APIDefaults
from football_predict_system.core.logging import get_logger, setup_logging


def test_settings_import() -> None:
    """测试设置模块导入"""
    settings = get_settings()
    assert settings is not None
    print(f"Settings loaded: {type(settings).__name__}")


def test_settings_attributes() -> None:
    """测试设置属性"""
    settings = get_settings()

    # 验证基础属性存在
    assert hasattr(settings, "api")
    assert hasattr(settings, "database")
    assert hasattr(settings.api, "host")
    assert hasattr(settings.api, "port")

    print(f"API Host: {settings.api.host}")
    print(f"API Port: {settings.api.port}")


def test_settings_defaults() -> None:
    """测试设置默认值"""

    # 创建默认设置实例
    settings = Settings()

    # 验证默认端口
    assert settings.api.port == APIDefaults.DEFAULT_PORT


def test_logging_setup() -> None:
    """测试日志设置"""
    # 测试日志系统初始化
    setup_logging()

    # 创建日志记录器并测试基本功能
    logger = get_logger("test_logger")
    assert logger is not None

    # 测试日志级别设置
    logger.info("Test info message")
    logger.debug("Test debug message")
    logger.warning("Test warning message")

    # 验证日志记录器有必要的方法
    assert hasattr(logger, "info")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")
    assert hasattr(logger, "critical")
