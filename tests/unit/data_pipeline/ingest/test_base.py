import pandas as pd
import pytest

from data_pipeline.ingest.base import (
    DataSource,
    DataSourceError,
    MatchDataSource,
    OddsDataSource,
)


# A concrete implementation for testing the base DataSource
class ConcreteDataSource(DataSource):
    def fetch(self) -> pd.DataFrame:
        pass

    def validate(self, df: pd.DataFrame) -> bool:
        pass


# 1. Test DataSource
def test_data_source_init_with_config():
    """Tests that DataSource initializes with a config."""
    config = {"key": "value"}
    ds = ConcreteDataSource(config=config)
    assert ds.config == config


def test_data_source_init_with_none_config():
    """Tests that DataSource initializes with an empty dict if config is None."""
    ds = ConcreteDataSource(config=None)
    assert ds.config == {}


# 2. Test MatchDataSource
class ConcreteMatchDataSource(MatchDataSource):
    """A concrete implementation of MatchDataSource for testing."""

    def fetch(self) -> pd.DataFrame:
        # This is an abstract method, so we need to implement it.
        pass


def test_match_data_source_validate_success():
    """Tests that MatchDataSource.validate returns True for a valid DataFrame."""
    source = ConcreteMatchDataSource()
    valid_df = pd.DataFrame(
        {
            "id": [1],
            "date": ["2023-01-01"],
            "home": [10],
            "away": [11],
            "home_goals": [2],
            "away_goals": [1],
            "result": ["H"],
        }
    )
    assert source.validate(valid_df) is True


def test_match_data_source_validate_failure():
    """Tests that MatchDataSource.validate returns False for an invalid DataFrame."""
    source = ConcreteMatchDataSource()
    invalid_df = pd.DataFrame(
        {
            "id": [1],
            "date": ["2023-01-01"],
            # Missing 'home' column
            "away": [11],
            "home_goals": [2],
            "away_goals": [1],
            "result": ["H"],
        }
    )
    assert source.validate(invalid_df) is False


# 3. Test OddsDataSource
class ConcreteOddsDataSource(OddsDataSource):
    """A concrete implementation of OddsDataSource for testing."""

    def fetch(self) -> pd.DataFrame:
        # This is an abstract method, so we need to implement it.
        pass


def test_odds_data_source_validate_success():
    """Tests that OddsDataSource.validate returns True for a valid DataFrame."""
    source = ConcreteOddsDataSource()
    valid_df = pd.DataFrame(
        {
            "id": [100],
            "match_id": [1],
            "h": [1.5],
            "d": [3.0],
            "a": [5.0],
            "provider": ["provider_a"],
        }
    )
    assert source.validate(valid_df) is True


def test_odds_data_source_validate_failure():
    """Tests that OddsDataSource.validate returns False for an invalid DataFrame."""
    source = ConcreteOddsDataSource()
    invalid_df = pd.DataFrame(
        {
            "id": [100],
            "match_id": [1],
            "h": [1.5],
            # Missing 'd' column
            "a": [5.0],
            "provider": ["provider_a"],
        }
    )
    assert source.validate(invalid_df) is False


# 4. Test DataSourceError
def test_data_source_error():
    """Tests that DataSourceError can be raised."""
    with pytest.raises(DataSourceError, match="Test error"):
        raise DataSourceError("Test error")
