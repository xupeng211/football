"""
Centralized configuration management for the football prediction system.

This module provides a unified configuration system that supports:
- Environment-specific configurations
- Type validation
- Configuration validation
- Secret management
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseSettings, Field, validator


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""

    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    echo: bool = Field(default=False, env="DB_ECHO")

    @validator("url")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "sqlite://", "mysql://")):
            raise ValueError(
                "Database URL must start with postgresql://, sqlite://, or mysql://"
            )
        return v


class RedisConfig(BaseSettings):
    """Redis configuration settings."""

    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    retry_on_timeout: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")


class APIConfig(BaseSettings):
    """API server configuration settings."""

    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    workers: int = Field(default=4, env="API_WORKERS")
    reload: bool = Field(default=False, env="API_RELOAD")
    log_level: str = Field(default="info", env="API_LOG_LEVEL")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # CORS
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")
    max_file_size: int = Field(default=10485760, env="LOG_MAX_FILE_SIZE")  # 10MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    # Structured logging
    service_name: str = Field(default="football-predict-system", env="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SERVICE_VERSION")

    @validator("level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration."""

    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    # Health checks
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    # Tracing
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")

    # Alerting
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    pagerduty_integration_key: Optional[str] = Field(
        default=None, env="PAGERDUTY_INTEGRATION_KEY"
    )


class MLConfig(BaseSettings):
    """Machine learning configuration settings."""

    model_registry_path: str = Field(
        default="models/artifacts", env="MODEL_REGISTRY_PATH"
    )
    default_model_version: Optional[str] = Field(
        default=None, env="DEFAULT_MODEL_VERSION"
    )

    # Training
    train_test_split: float = Field(default=0.2, env="TRAIN_TEST_SPLIT")
    random_state: int = Field(default=42, env="RANDOM_STATE")

    # XGBoost specific
    xgb_n_estimators: int = Field(default=100, env="XGB_N_ESTIMATORS")
    xgb_max_depth: int = Field(default=6, env="XGB_MAX_DEPTH")
    xgb_learning_rate: float = Field(default=0.1, env="XGB_LEARNING_RATE")

    @validator("train_test_split")
    def validate_train_test_split(cls, v: float) -> float:
        """Validate train/test split ratio."""
        if not 0.1 <= v <= 0.5:
            raise ValueError("Train/test split must be between 0.1 and 0.5")
        return v


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    api: APIConfig = APIConfig()
    logging: LoggingConfig = LoggingConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    ml: MLConfig = MLConfig()

    # Application specific
    app_name: str = Field(default="Football Prediction System", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("environment", pre=True)
    def parse_environment(cls, v):
        """Parse environment from string."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT

    def get_database_url(self) -> str:
        """Get database URL with environment-specific modifications."""
        if self.is_development() and "@db:" in self.database.url:
            return self.database.url.replace("@db:", "@localhost:")
        return self.database.url


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global settings
    settings = Settings()
    return settings
