"""
项目常量定义

用于替代代码中的魔法数字, 提高代码可读性和可维护性。
"""


# HTTP状态码常量
class HTTPStatus:
    OK = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# API相关常量
class APIDefaults:
    DEFAULT_PORT = 8000
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3


# 测试相关常量
class TestConstants:
    # 性能测试相关
    PERFORMANCE_TOLERANCE = 0.001
    SLOW_QUERY_THRESHOLD_MS = 1000.0
    FAST_QUERY_THRESHOLD_MS = 500.0

    # 特征向量长度
    FEATURE_VECTOR_LENGTH = 6

    # 测试数据值
    HOME_STRENGTH_SAMPLE = 0.7
    HOME_ODDS_SAMPLE = 1.8
    ODDS_THRESHOLD = 1.5

    # 批量处理
    BATCH_SIZE_SMALL = 2
    BATCH_SIZE_MEDIUM = 3
    BATCH_SIZE_LARGE = 5
    BATCH_SIZE_XL = 10

    # 时间相关
    TIMEOUT_SECONDS = 5

    # 神经网络相关
    MAGIC_NUMBER_42 = 42


# 健康检查相关常量
class HealthConstants:
    LATENCY_MS_HEALTHY = 50
    COMPONENT_COUNT_FULL = 5


# 缓存相关常量
class CacheConstants:
    DEFAULT_TTL = 300  # 5分钟
    TIMESTAMP_SAMPLE = 1234567890.123


# 数据库相关常量
class DatabaseConstants:
    CONNECTION_POOL_SIZE = 10
    QUERY_TIMEOUT = 30
