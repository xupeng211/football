"""
Centralized configuration management for the football prediction system.

This module provides a unified configuration system that supports:
- Environment-specific configurations
- Type validation
- Configuration validation
- Secret management
"""

import os
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseModel):
    """Database configuration settings."""

    url: str = "sqlite:///./test.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    @field_validator("url")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "sqlite://", "mysql://")):
            raise ValueError(
                "Database URL must start with postgresql://, sqlite://, or mysql://"
            )
        return v


class RedisConfig(BaseModel):
    """Redis configuration settings."""

    url: str = "redis://localhost:6379/0"
    max_connections: int = 10
    retry_on_timeout: bool = True
    socket_timeout: int = 5


class APIConfig(BaseModel):
    """API server configuration settings."""

    host: str = Field(
        default="127.0.0.1",
        description="Host to bind to. Use 0.0.0.0 only in production",
    )
    port: int = 8000
    workers: int = 4
    reload: bool = False
    log_level: str = "info"

    # Security
    secret_key: str = Field(
        default_factory=lambda: os.urandom(32).hex(),
        description="API secret key - use env var in production",
    )
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    @field_validator("cors_origins", mode="before")
    def parse_cors_origins(cls, v: Any) -> Any:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class LoggingConfig(BaseModel):
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "json"  # json or text
    file_path: str | None = None
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5

    # Structured logging
    service_name: str = "football-predict-system"
    service_version: str = "1.0.0"

    @field_validator("level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""

    enable_metrics: bool = True
    metrics_port: int = 9090

    # Health checks
    health_check_interval: int = 30

    # Tracing
    enable_tracing: bool = False
    jaeger_endpoint: str | None = None

    # Alerting
    slack_webhook_url: str | None = None
    pagerduty_integration_key: str | None = None


class MLConfig(BaseModel):
    """Machine learning configuration settings."""

    model_registry_path: str = "models/artifacts"
    default_model_version: str | None = None

    # Training
    train_test_split: float = 0.2
    random_state: int = 42

    # XGBoost specific
    xgb_n_estimators: int = 100
    xgb_max_depth: int = 6
    xgb_learning_rate: float = 0.1

    @field_validator("train_test_split")
    def validate_train_test_split(cls, v: float) -> float:
        """Validate train/test split ratio."""
        if not 0.1 <= v <= 0.5:
            raise ValueError("Train/test split must be between 0.1 and 0.5")
        return v


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Direct environment variable support
    database_url: str = Field(default="sqlite:///./test.db")
    redis: RedisConfig = Field(default_factory=RedisConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    ml: MLConfig = Field(default_factory=MLConfig)

    # Application specific
    app_name: str = "Football Prediction System"
    app_version: str = "1.0.0"

    # JWT Configuration (for backward compatibility)
    jwt_secret_key: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(
        default=30, description="JWT expiration time in minutes"
    )

    # Redis URL (for backward compatibility)
    redis_url: str = Field(default="", description="Redis connection URL")
    redis_password: str = Field(default="", description="Redis password")

    def model_post_init(self, __context: Any) -> None:
        """Post initialization to sync values."""
        # Sync JWT settings with API config if not explicitly set
        if not self.jwt_secret_key:
            self.jwt_secret_key = self.api.secret_key
        else:
            # If explicitly set, update API config
            self.api.secret_key = self.jwt_secret_key

        if self.jwt_expire_minutes != 30:  # If changed from default
            self.api.access_token_expire_minutes = self.jwt_expire_minutes
        else:
            self.jwt_expire_minutes = self.api.access_token_expire_minutes

        # Sync Redis URL
        if not self.redis_url:
            self.redis_url = self.redis.url
        else:
            # If explicitly set, update Redis config
            self.redis.url = self.redis_url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",  # 忽略额外的环境变量字段
    )

    @field_validator("environment", mode="before")
    def parse_environment(cls, v: Any) -> Any:
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
        # Use direct environment variable if available, otherwise fallback
        db_url = (
            self.database_url if hasattr(self, "database_url") else self.database.url
        )
        if self.is_development() and "@db:" in db_url:
            return db_url.replace("@db:", "@localhost:")
        return db_url


# Global settings instance (lazy initialization)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings instance."""
    global _settings
    # Handle case where _settings might be deleted by tests
    if "_settings" not in globals() or _settings is None:
        _settings = Settings()
    return _settings


# Initialize settings for backward compatibility
settings = get_settings()


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
