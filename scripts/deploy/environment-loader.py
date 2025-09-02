#!/usr/bin/env python3
"""
Environment Configuration Loader for Multi-Environment Deployment

This script manages loading and validation of environment-specific configurations
for development, staging, and production deployments.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class Environment(str, Enum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentConfig:
    """Environment configuration container."""

    name: str
    config_file: Path
    required_secrets: list
    optional_secrets: list
    validation_rules: dict


class EnvironmentLoader:
    """Manages environment configuration loading and validation."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.configs_dir = self.project_root / "configs" / "environments"

        # Environment configurations
        self.environments = {
            Environment.DEVELOPMENT: EnvironmentConfig(
                name="development",
                config_file=self.configs_dir / "development.env",
                required_secrets=[],
                optional_secrets=["FOOTBALL_DATA_API_KEY", "OPENAI_API_KEY"],
                validation_rules={
                    "DEBUG": True,
                    "LOG_LEVEL": "debug",
                    "API_WORKERS": 1,
                },
            ),
            Environment.STAGING: EnvironmentConfig(
                name="staging",
                config_file=self.configs_dir / "staging.env",
                required_secrets=[
                    "STAGING_DATABASE_URL",
                    "STAGING_REDIS_URL",
                    "STAGING_SECRET_KEY",
                ],
                optional_secrets=[
                    "STAGING_FOOTBALL_DATA_API_KEY",
                    "STAGING_OPENAI_API_KEY",
                ],
                validation_rules={
                    "DEBUG": False,
                    "LOG_LEVEL": "info",
                    "API_WORKERS": 2,
                },
            ),
            Environment.PRODUCTION: EnvironmentConfig(
                name="production",
                config_file=self.configs_dir / "production.env",
                required_secrets=[
                    "PRODUCTION_DATABASE_URL",
                    "PRODUCTION_REDIS_URL",
                    "PRODUCTION_SECRET_KEY",
                    "PRODUCTION_FOOTBALL_DATA_API_KEY",
                ],
                optional_secrets=["PRODUCTION_OPENAI_API_KEY"],
                validation_rules={
                    "DEBUG": False,
                    "LOG_LEVEL": "warning",
                    "API_WORKERS": 4,
                },
            ),
        }

    def load_environment(self, env: Environment) -> dict[str, Any]:
        """Load and validate environment configuration."""
        config = self.environments[env]

        print(f"🔧 Loading {env.value} environment configuration...")

        # Check if config file exists
        if not config.config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config.config_file}"
            )

        # Load configuration
        env_vars = self._load_env_file(config.config_file)

        # Validate required secrets
        self._validate_secrets(env, env_vars)

        # Apply validation rules
        self._validate_configuration(env, env_vars)

        print(f"✅ {env.value} environment loaded successfully")
        return env_vars

    def _load_env_file(self, env_file: Path) -> dict[str, Any]:
        """Load environment variables from file."""
        env_vars = {}

        with open(env_file) as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if line.startswith("#") or not line:
                    continue

                # Parse key=value pairs
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    env_vars[key] = value

        return env_vars

    def _validate_secrets(self, env: Environment, env_vars: dict[str, Any]):
        """Validate that required secrets are available."""
        config = self.environments[env]
        missing_secrets = []

        for secret in config.required_secrets:
            # Check if secret is available in environment or as interpolated value
            if secret not in os.environ and f"${{{secret}}}" in str(env_vars.values()):
                missing_secrets.append(secret)

        if missing_secrets:
            print(f"❌ Missing required secrets for {env.value}:")
            for secret in missing_secrets:
                print(f"   - {secret}")

            if env == Environment.PRODUCTION:
                raise ValueError(
                    "Production deployment requires all secrets to be configured"
                )
            else:
                print(f"⚠️  Warning: Missing secrets for {env.value} environment")

    def _validate_configuration(self, env: Environment, env_vars: dict[str, Any]):
        """Validate configuration against rules."""
        config = self.environments[env]

        for key, expected_value in config.validation_rules.items():
            if key in env_vars:
                actual_value = env_vars[key]

                # Type conversion for comparison
                if isinstance(expected_value, bool):
                    actual_value = actual_value.lower() in ("true", "1", "yes", "on")
                elif isinstance(expected_value, int):
                    try:
                        actual_value = int(actual_value)
                    except ValueError:
                        pass

                if actual_value != expected_value:
                    print(
                        f"⚠️  Configuration mismatch for {key}: expected {expected_value}, got {actual_value}"
                    )

    def export_environment(self, env: Environment, output_file: Path | None = None):
        """Export environment configuration to a file."""
        env_vars = self.load_environment(env)

        if output_file is None:
            output_file = self.project_root / f".env.{env.value}"

        print(f"📝 Exporting {env.value} configuration to {output_file}")

        with open(output_file, "w") as f:
            f.write(f"# {env.value.title()} Environment Configuration\n")
            f.write("# Generated by environment-loader.py\n\n")

            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        print(f"✅ Configuration exported to {output_file}")

    def validate_environment(self, env: Environment) -> bool:
        """Validate environment configuration without loading."""
        try:
            self.load_environment(env)
            return True
        except Exception as e:
            print(f"❌ Environment validation failed: {e}")
            return False

    def list_environments(self):
        """List available environments and their status."""
        print("📋 Available Environments:")
        print("=" * 50)

        for env in Environment:
            config = self.environments[env]
            status = "✅" if config.config_file.exists() else "❌"

            print(f"{status} {env.value.title()}")
            print(f"   Config: {config.config_file}")
            print(f"   Required secrets: {len(config.required_secrets)}")
            print(f"   Optional secrets: {len(config.optional_secrets)}")
            print()


def _handle_list_command(loader: EnvironmentLoader) -> None:
    """Handle list command."""
    loader.list_environments()


def _handle_validate_command(loader: EnvironmentLoader, env: Environment) -> None:
    """Handle validate command."""
    if loader.validate_environment(env):
        print(f"✅ {env.value} environment is valid")
        sys.exit(0)
    else:
        sys.exit(1)


def _handle_load_command(loader: EnvironmentLoader, env: Environment) -> None:
    """Handle load command."""
    config = loader.load_environment(env)

    # Print loaded configuration (excluding secrets)
    print(f"\n📋 Loaded Configuration for {env.value}:")
    for key, value in config.items():
        if any(
            secret_word in key.lower()
            for secret_word in ["password", "secret", "key", "token"]
        ):
            print(f"   {key}=***")
        else:
            print(f"   {key}={value}")


def _handle_export_command(loader: EnvironmentLoader, env: Environment, output: Path) -> None:
    """Handle export command."""
    loader.export_environment(env, output)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Environment Configuration Loader for Football Prediction System"
    )

    parser.add_argument(
        "command",
        choices=["load", "validate", "export", "list"],
        help="Command to execute",
    )

    parser.add_argument(
        "--env",
        type=str,
        choices=[e.value for e in Environment],
        help="Target environment",
    )

    parser.add_argument("--output", type=Path, help="Output file for export command")

    args = parser.parse_args()
    loader = EnvironmentLoader()

    try:
        if args.command == "list":
            _handle_list_command(loader)
        elif args.command == "validate":
            if not args.env:
                parser.error("--env is required for validate command")
            _handle_validate_command(loader, Environment(args.env))
        elif args.command == "load":
            if not args.env:
                parser.error("--env is required for load command")
            _handle_load_command(loader, Environment(args.env))
        elif args.command == "export":
            if not args.env:
                parser.error("--env is required for export command")
            _handle_export_command(loader, Environment(args.env), args.output)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
