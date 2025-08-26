# apps/api/core/settings.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    app_port: int = 8000
    api_host: str = "127.0.0.1"  # nosec B104
    api_debug: bool = False
    api_secret_key: str = "default-secret-key"

    # 数据库配置
    database_url: str = "postgresql://postgres:postgres@localhost:5432/sports"
    pg_password: str | None = None

    # Redis配置
    redis_url: str = "redis://localhost:6379"

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "console"

    # 模型配置
    model_version: str = "latest"
    model_registry_path: str = "./models/artifacts"
    model_cache_size: int = 10

    # 数据源配置
    football_api_key: str | None = None
    data_update_interval_minutes: int = 60

    # 监控配置
    monitoring_enabled: bool = True
    metrics_port: int = 9090

    # Prefect配置
    prefect_api_url: str = "http://localhost:4200/api"

    # 特征配置
    feature_set: str = "v1"

    # 回测配置
    backtest_start_date: str | None = None
    backtest_end_date: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量


settings = Settings()
