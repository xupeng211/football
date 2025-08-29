# apps/api/core/settings.py

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用配置
    app_port: int = 8000
    api_host: str = "127.0.0.1"  # nosec B104
    api_debug: bool = False
    api_secret_key: str = Field(
        default="dev-secret-key-change-in-prod",
        description="API secret key - MUST be changed in production",
    )

    # 数据库配置
    @property
    def database_url(self) -> str:
        if os.getenv("PYTEST_CURRENT_TEST"):
            return "sqlite:///:memory:"
        default_db = "postgresql://postgres:postgres@localhost:5432/sports"
        return os.getenv("DATABASE_URL", default_db) or "sqlite:///:memory:"

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

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


settings = Settings()
