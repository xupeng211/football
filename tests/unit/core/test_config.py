"""Tests for core config module."""

import os
from unittest.mock import Mock, patch

from football_predict_system.core.config import Settings, get_settings


class TestSettings:
    """Test Settings class."""

    def test_settings_creation(self):
        """Test creating Settings instance with defaults."""
        settings = Settings()

        assert settings is not None
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'jwt_secret_key')
        assert hasattr(settings, 'debug')

    def test_settings_debug_mode(self):
        """Test debug mode setting."""
        with patch.dict(os.environ, {'DEBUG': 'true'}):
            settings = Settings()
            assert settings.debug is True

        with patch.dict(os.environ, {'DEBUG': 'false'}):
            settings = Settings()
            assert settings.debug is False

    def test_settings_database_url(self):
        """Test database URL setting."""
        test_url = "postgresql://test:test@localhost/test"
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            settings = Settings()
            assert settings.database_url == test_url

    def test_settings_jwt_configuration(self):
        """Test JWT configuration."""
        with patch.dict(os.environ, {
            'JWT_SECRET_KEY': 'test_secret',
            'JWT_ALGORITHM': 'HS256',
            'JWT_EXPIRE_MINUTES': '60'
        }):
            settings = Settings()
            assert settings.jwt_secret_key == 'test_secret'
            assert settings.jwt_algorithm == 'HS256'
            assert settings.jwt_expire_minutes == 60

    def test_settings_redis_configuration(self):
        """Test Redis configuration."""
        with patch.dict(os.environ, {
            'REDIS_URL': 'redis://localhost:6380',
            'REDIS_PASSWORD': 'test_password'
        }):
            settings = Settings()
            assert settings.redis_url == 'redis://localhost:6380'
            assert settings.redis_password == 'test_password'


class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()

        assert isinstance(settings, Settings)

    @patch('football_predict_system.core.config.Settings')
    def test_get_settings_creates_only_once(self, mock_settings):
        """Test that Settings is only instantiated once."""
        mock_instance = Mock()
        mock_settings.return_value = mock_instance

        # Clear any existing singleton
        import football_predict_system.core.config as config_module
        if hasattr(config_module, '_settings'):
            delattr(config_module, '_settings')

        # Call get_settings multiple times
        settings1 = get_settings()
        settings2 = get_settings()

        # Should only create Settings once
        mock_settings.assert_called_once()
        assert settings1 == mock_instance
        assert settings2 == mock_instance


class TestSettingsValidation:
    """Test Settings validation."""

    def test_settings_with_empty_environment(self):
        """Test Settings creation with minimal environment variables."""
        # Clear relevant environment variables
        env_vars_to_clear = [
            'DATABASE_URL', 'JWT_SECRET_KEY', 'REDIS_URL', 'DEBUG'
        ]

        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]

            # This should still work with defaults
            settings = Settings()
            assert settings is not None

    def test_settings_bool_conversion(self):
        """Test boolean environment variable conversion."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('1', True),
            ('0', False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'DEBUG': env_value}):
                settings = Settings()
                assert settings.debug == expected

    def test_settings_integer_conversion(self):
        """Test integer environment variable conversion."""
        with patch.dict(os.environ, {
            'JWT_EXPIRE_MINUTES': '120',
            'DATABASE_POOL_SIZE': '20'
        }):
            settings = Settings()
            assert settings.jwt_expire_minutes == 120
            if hasattr(settings, 'database_pool_size'):
                assert settings.database_pool_size == 20
