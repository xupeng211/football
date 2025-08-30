import importlib
import os
import sys
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from apps.api import db
from apps.api.db import _is_testing, check_db_connection, init_db


@patch("apps.api.db.load_dotenv", lambda: None)
class TestIsTesting:
    def test_is_testing_pytest_current_test(self):
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "some_test"}):
            assert _is_testing() is True

    def test_is_testing_pytest_in_underscore(self):
        with patch.dict(os.environ, {"_": "/path/to/pytest"}):
            assert _is_testing() is True

    def test_is_testing_pytest_in_sys_argv(self):
        with patch.object(sys, "argv", ["/path/to/pytest", "arg1"]):
            assert _is_testing() is True

    def test_is_testing_false(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(sys, "argv", ["script.py"]):
                assert _is_testing() is False


@patch("apps.api.db.load_dotenv", lambda: None)
class TestDatabaseUrlLogic:
    @patch("apps.api.db._is_testing", return_value=False)
    def test_database_url_production(self, mock_is_testing):
        with patch.dict(os.environ, {"DATABASE_URL": "prod_db_url"}, clear=True):
            importlib.reload(db)
            assert db.DATABASE_URL == "prod_db_url"

    def test_database_url_is_testing(self):
        with patch.dict(os.environ, {}, clear=True), patch(
            "dotenv.load_dotenv", lambda: None
        ), patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "true"}):
            importlib.reload(db)
            assert db.DATABASE_URL == "sqlite:///:memory:"

    def test_database_url_test_db_url_priority(self):
        with patch.dict(os.environ, {"TEST_DATABASE_URL": "test_db_url"}, clear=True):
            importlib.reload(db)
            assert db.DATABASE_URL == "test_db_url"

    @patch("apps.api.db._is_testing", return_value=False)
    def test_database_url_not_set_error(self, mock_is_testing):
        with patch.dict(os.environ, {}, clear=True):
            with patch("dotenv.load_dotenv", lambda: None):
                with pytest.raises(ValueError, match="DATABASE_URL must be set"):
                    importlib.reload(db)


@patch("apps.api.db.load_dotenv", lambda: None)
class TestInitDb:
    def test_init_db_with_url(self):
        init_db("sqlite:///:memory:")
        assert db.engine is not None

    @patch("apps.api.db._is_testing", return_value=False)
    def test_init_db_no_url_raises_error(self, mock_is_testing):
        with patch.dict(os.environ, {}, clear=True):
            with patch("dotenv.load_dotenv", lambda: None):
                with pytest.raises(ValueError, match="Database URL is not configured"):
                    init_db()

    @patch("apps.api.db.create_engine")
    @patch("apps.api.db._is_testing", return_value=False)
    def test_init_db_dev_environment_url_replace(
        self, mock_is_testing, mock_create_engine
    ):
        dev_url = "postgresql://user:pass@db:5432/testdb"
        expected_url = "postgresql://user:pass@localhost:5432/testdb"
        env_vars = {"ENV": "development", "DATABASE_URL": dev_url}
        with patch.dict(os.environ, env_vars, clear=True):
            init_db()
            mock_create_engine.assert_called_once_with(expected_url)


@patch("apps.api.db.load_dotenv", lambda: None)
class TestCheckDbConnection:
    def test_check_db_connection_not_initialized_in_prod(self):
        db.engine = None
        with patch("apps.api.db._is_testing", return_value=False):
            connected, message = check_db_connection()
            assert connected is False
            assert message == "Database engine not initialized."

    def test_check_db_connection_initializes_in_test(self):
        db.engine = None
        with patch("apps.api.db._is_testing", return_value=True):
            connected, message = check_db_connection()
            assert connected is True
            assert message == "Database connection successful."
            assert db.engine is not None

    def test_check_db_connection_sqlalchemy_error(self):
        init_db("sqlite:///:memory:")
        with patch.object(
            db.engine,
            "connect",
            side_effect=SQLAlchemyError("Connection failed"),
        ):
            connected, message = check_db_connection()
            assert connected is False
            assert "Database connection failed: Connection failed" in message

    def test_check_db_connection_init_fails(self):
        db.engine = None
        with patch("apps.api.db.init_db", side_effect=ValueError("Config error")):
            with patch("apps.api.db._is_testing", return_value=True):
                with pytest.raises(ValueError, match="Config error"):
                    check_db_connection()

        db.engine = None
        with patch("apps.api.db.init_db", lambda: None):
            with patch("apps.api.db._is_testing", return_value=True):
                connected, message = check_db_connection()
                assert connected is False
                assert message == "Database engine failed to initialize."
