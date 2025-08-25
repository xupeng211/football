import os

import pytest
from sqlalchemy import create_engine, inspect


@pytest.fixture(scope="module")
def db_engine():
    """Provides a SQLAlchemy engine for the test session."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/sports")
    engine = create_engine(db_url)
    yield engine
    engine.dispose()


def test_db_connection(db_engine):
    """Tests that the database connection can be established."""
    try:
        connection = db_engine.connect()
        connection.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")


def test_tables_exist(db_engine):
    """Tests that the required tables exist in the database."""
    inspector = inspect(db_engine)
    tables = inspector.get_table_names()
    assert "matches" in tables
    assert "odds" in tables
