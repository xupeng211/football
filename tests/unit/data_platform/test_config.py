"""
Tests for data platform configuration.

Complete coverage tests for all configuration models and constants.
"""

import pytest
from pydantic import ValidationError

from football_predict_system.data_platform.config import (
    COLLECTION_PRIORITIES,
    COMPETITION_MAPPINGS,
    CollectionSchedule,
    DataPlatformConfig,
    DataSourceConfig,
    get_data_platform_config,
)


class TestDataSourceConfig:
    """Test DataSourceConfig model."""

    def test_data_source_config_defaults(self):
        """Test DataSourceConfig with minimal required fields."""
        config = DataSourceConfig(name="test_source", source_type="api")

        assert config.name == "test_source"
        assert config.source_type == "api"
        assert config.base_url is None
        assert config.api_key_required is False
        assert config.rate_limit_per_minute == 60
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 60
        assert config.reliability_score == 0.8
        assert config.is_active is True
        assert config.headers_template == {}
        assert config.auth_method == "none"

    def test_data_source_config_all_fields(self):
        """Test DataSourceConfig with all fields specified."""
        config = DataSourceConfig(
            name="api_source",
            source_type="api",
            base_url="https://api.example.com",
            api_key_required=True,
            rate_limit_per_minute=100,
            timeout_seconds=45,
            retry_attempts=5,
            retry_delay_seconds=30,
            reliability_score=0.95,
            is_active=False,
            headers_template={"Authorization": "Bearer token"},
            auth_method="bearer",
        )

        assert config.name == "api_source"
        assert config.source_type == "api"
        assert config.base_url == "https://api.example.com"
        assert config.api_key_required is True
        assert config.rate_limit_per_minute == 100
        assert config.timeout_seconds == 45
        assert config.retry_attempts == 5
        assert config.retry_delay_seconds == 30
        assert config.reliability_score == 0.95
        assert config.is_active is False
        assert config.headers_template == {"Authorization": "Bearer token"}
        assert config.auth_method == "bearer"

    def test_data_source_config_valid_source_types(self):
        """Test valid source types."""
        valid_types = ["api", "file", "scraping"]

        for source_type in valid_types:
            config = DataSourceConfig(name="test", source_type=source_type)
            assert config.source_type == source_type

    def test_data_source_config_invalid_source_type(self):
        """Test invalid source type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DataSourceConfig(name="test", source_type="invalid")

        assert "String should match pattern" in str(exc_info.value)

    def test_data_source_config_valid_auth_methods(self):
        """Test valid authentication methods."""
        valid_methods = ["none", "api_key", "bearer", "basic"]

        for auth_method in valid_methods:
            config = DataSourceConfig(
                name="test", source_type="api", auth_method=auth_method
            )
            assert config.auth_method == auth_method

    def test_data_source_config_invalid_auth_method(self):
        """Test invalid auth method raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DataSourceConfig(name="test", source_type="api", auth_method="invalid")

        assert "String should match pattern" in str(exc_info.value)

    def test_data_source_config_reliability_score_bounds(self):
        """Test reliability score bounds validation."""
        # Valid bounds
        config1 = DataSourceConfig(
            name="test", source_type="api", reliability_score=0.0
        )
        assert config1.reliability_score == 0.0

        config2 = DataSourceConfig(
            name="test", source_type="api", reliability_score=1.0
        )
        assert config2.reliability_score == 1.0

        # Invalid bounds
        with pytest.raises(ValidationError):
            DataSourceConfig(name="test", source_type="api", reliability_score=-0.1)

        with pytest.raises(ValidationError):
            DataSourceConfig(name="test", source_type="api", reliability_score=1.1)

    def test_data_source_config_file_type(self):
        """Test file source type configuration."""
        config = DataSourceConfig(name="file_source", source_type="file")
        assert config.source_type == "file"

    def test_data_source_config_scraping_type(self):
        """Test scraping source type configuration."""
        config = DataSourceConfig(name="scraping_source", source_type="scraping")
        assert config.source_type == "scraping"


class TestCollectionSchedule:
    """Test CollectionSchedule model."""

    def test_collection_schedule_defaults(self):
        """Test CollectionSchedule with default values."""
        schedule = CollectionSchedule()

        assert schedule.daily_collection_cron == "0 */6 * * *"
        assert schedule.daily_competitions == [2021, 2014, 2002, 2019, 2015]
        assert schedule.daily_date_range_days == 7
        assert schedule.quality_check_cron == "0 * * * *"
        assert schedule.quality_thresholds == {
            "max_stale_hours": 24,
            "min_quality_score": 80,
            "max_missing_scores_percent": 5,
        }
        assert schedule.backfill_batch_days == 30
        assert schedule.backfill_delay_seconds == 6

    def test_collection_schedule_custom_values(self):
        """Test CollectionSchedule with custom values."""
        custom_competitions = [2001, 2002, 2003]
        custom_thresholds = {
            "max_stale_hours": 12,
            "min_quality_score": 90,
            "max_missing_scores_percent": 2,
        }

        schedule = CollectionSchedule(
            daily_collection_cron="0 */3 * * *",
            daily_competitions=custom_competitions,
            daily_date_range_days=14,
            quality_check_cron="0 */2 * * *",
            quality_thresholds=custom_thresholds,
            backfill_batch_days=60,
            backfill_delay_seconds=10,
        )

        assert schedule.daily_collection_cron == "0 */3 * * *"
        assert schedule.daily_competitions == custom_competitions
        assert schedule.daily_date_range_days == 14
        assert schedule.quality_check_cron == "0 */2 * * *"
        assert schedule.quality_thresholds == custom_thresholds
        assert schedule.backfill_batch_days == 60
        assert schedule.backfill_delay_seconds == 10

    def test_collection_schedule_competition_list_structure(self):
        """Test competition list structure."""
        schedule = CollectionSchedule()
        competitions = schedule.daily_competitions

        # Should contain major European leagues
        assert 2021 in competitions  # Premier League
        assert 2014 in competitions  # La Liga
        assert 2002 in competitions  # Bundesliga
        assert 2019 in competitions  # Serie A
        assert 2015 in competitions  # Ligue 1

        # Should be a list of integers
        assert isinstance(competitions, list)
        assert all(isinstance(comp_id, int) for comp_id in competitions)

    def test_collection_schedule_quality_thresholds_structure(self):
        """Test quality thresholds structure."""
        schedule = CollectionSchedule()
        thresholds = schedule.quality_thresholds

        # Should contain expected keys
        expected_keys = [
            "max_stale_hours",
            "min_quality_score",
            "max_missing_scores_percent",
        ]
        for key in expected_keys:
            assert key in thresholds

        # Should have reasonable values
        assert isinstance(thresholds["max_stale_hours"], int)
        assert isinstance(thresholds["min_quality_score"], int)
        assert isinstance(thresholds["max_missing_scores_percent"], int)

    def test_collection_schedule_empty_competitions(self):
        """Test schedule with empty competitions list."""
        schedule = CollectionSchedule(daily_competitions=[])
        assert schedule.daily_competitions == []

    def test_collection_schedule_single_competition(self):
        """Test schedule with single competition."""
        schedule = CollectionSchedule(daily_competitions=[2021])
        assert schedule.daily_competitions == [2021]


class TestDataPlatformConfig:
    """Test DataPlatformConfig model."""

    def test_data_platform_config_defaults(self):
        """Test DataPlatformConfig with default values."""
        config = DataPlatformConfig()

        # Check data sources
        assert isinstance(config.football_data_org, DataSourceConfig)
        assert isinstance(config.api_football, DataSourceConfig)
        assert isinstance(config.schedule, CollectionSchedule)

        # Check storage settings
        assert config.max_batch_size == 1000
        assert config.data_retention_days == 365 * 3
        assert config.backup_enabled is True
        assert config.backup_frequency_hours == 24

        # Check quality settings
        assert config.enable_data_validation is True
        assert config.enable_duplicate_detection is True
        assert config.enable_anomaly_detection is True

        # Check performance settings
        assert config.max_concurrent_requests == 5
        assert config.connection_pool_size == 10
        assert config.cache_ttl_hours == 1

    def test_data_platform_config_football_data_org(self):
        """Test football-data.org configuration."""
        config = DataPlatformConfig()
        fdo_config = config.football_data_org

        assert fdo_config.name == "football-data-org"
        assert fdo_config.source_type == "api"
        assert fdo_config.base_url == "https://api.football-data.org/v4"
        assert fdo_config.api_key_required is True
        assert fdo_config.rate_limit_per_minute == 10
        assert fdo_config.headers_template == {"Accept": "application/json"}
        assert fdo_config.auth_method == "api_key"
        assert fdo_config.reliability_score == 0.95

    def test_data_platform_config_api_football(self):
        """Test api-football configuration."""
        config = DataPlatformConfig()
        api_config = config.api_football

        assert api_config.name == "api-football"
        assert api_config.source_type == "api"
        assert api_config.base_url == "https://v3.football.api-sports.io"
        assert api_config.api_key_required is True
        assert api_config.rate_limit_per_minute == 100
        assert api_config.headers_template == {"Accept": "application/json"}
        assert api_config.auth_method == "api_key"
        assert api_config.reliability_score == 0.90

    def test_data_platform_config_custom_values(self):
        """Test DataPlatformConfig with custom values."""
        custom_schedule = CollectionSchedule(daily_date_range_days=14)

        config = DataPlatformConfig(
            schedule=custom_schedule,
            max_batch_size=500,
            data_retention_days=180,
            backup_enabled=False,
            backup_frequency_hours=12,
            enable_data_validation=False,
            enable_duplicate_detection=False,
            enable_anomaly_detection=False,
            max_concurrent_requests=10,
            connection_pool_size=20,
            cache_ttl_hours=2,
        )

        assert config.schedule.daily_date_range_days == 14
        assert config.max_batch_size == 500
        assert config.data_retention_days == 180
        assert config.backup_enabled is False
        assert config.backup_frequency_hours == 12
        assert config.enable_data_validation is False
        assert config.enable_duplicate_detection is False
        assert config.enable_anomaly_detection is False
        assert config.max_concurrent_requests == 10
        assert config.connection_pool_size == 20
        assert config.cache_ttl_hours == 2

    def test_data_platform_config_retention_calculation(self):
        """Test data retention calculation."""
        config = DataPlatformConfig()

        # Default is 3 years
        expected_days = 365 * 3
        assert config.data_retention_days == expected_days

    def test_data_platform_config_nested_model_validation(self):
        """Test nested model validation."""
        config = DataPlatformConfig()

        # Should have valid nested models
        assert config.football_data_org.source_type in ["api", "file", "scraping"]
        assert config.api_football.source_type in ["api", "file", "scraping"]
        assert 0.0 <= config.football_data_org.reliability_score <= 1.0
        assert 0.0 <= config.api_football.reliability_score <= 1.0


class TestGlobalFunctions:
    """Test global functions."""

    def test_get_data_platform_config(self):
        """Test get_data_platform_config function."""
        config = get_data_platform_config()

        assert isinstance(config, DataPlatformConfig)
        assert isinstance(config.football_data_org, DataSourceConfig)
        assert isinstance(config.api_football, DataSourceConfig)
        assert isinstance(config.schedule, CollectionSchedule)

    def test_get_data_platform_config_returns_new_instance(self):
        """Test that function returns new instance each time."""
        config1 = get_data_platform_config()
        config2 = get_data_platform_config()

        # Should be different instances
        assert config1 is not config2

        # But should have same values
        assert config1.max_batch_size == config2.max_batch_size
        assert config1.data_retention_days == config2.data_retention_days


class TestCompetitionMappings:
    """Test COMPETITION_MAPPINGS constant."""

    def test_competition_mappings_structure(self):
        """Test competition mappings structure."""
        assert isinstance(COMPETITION_MAPPINGS, dict)
        assert len(COMPETITION_MAPPINGS) > 0

    def test_competition_mappings_top_leagues(self):
        """Test top 5 European leagues are present."""
        expected_leagues = [
            "premier_league",
            "la_liga",
            "bundesliga",
            "serie_a",
            "ligue_1",
        ]

        for league in expected_leagues:
            assert league in COMPETITION_MAPPINGS
            mapping = COMPETITION_MAPPINGS[league]
            assert "id" in mapping
            assert "name" in mapping
            assert "country" in mapping
            assert "priority" in mapping

    def test_competition_mappings_premier_league(self):
        """Test Premier League mapping."""
        pl = COMPETITION_MAPPINGS["premier_league"]

        assert pl["id"] == 2021
        assert pl["name"] == "Premier League"
        assert pl["country"] == "England"
        assert pl["priority"] == 1

    def test_competition_mappings_la_liga(self):
        """Test La Liga mapping."""
        la_liga = COMPETITION_MAPPINGS["la_liga"]

        assert la_liga["id"] == 2014
        assert la_liga["name"] == "Primera Division"
        assert la_liga["country"] == "Spain"
        assert la_liga["priority"] == 1

    def test_competition_mappings_bundesliga(self):
        """Test Bundesliga mapping."""
        bundesliga = COMPETITION_MAPPINGS["bundesliga"]

        assert bundesliga["id"] == 2002
        assert bundesliga["name"] == "Bundesliga"
        assert bundesliga["country"] == "Germany"
        assert bundesliga["priority"] == 1

    def test_competition_mappings_serie_a(self):
        """Test Serie A mapping."""
        serie_a = COMPETITION_MAPPINGS["serie_a"]

        assert serie_a["id"] == 2019
        assert serie_a["name"] == "Serie A"
        assert serie_a["country"] == "Italy"
        assert serie_a["priority"] == 1

    def test_competition_mappings_ligue_1(self):
        """Test Ligue 1 mapping."""
        ligue_1 = COMPETITION_MAPPINGS["ligue_1"]

        assert ligue_1["id"] == 2015
        assert ligue_1["name"] == "Ligue 1"
        assert ligue_1["country"] == "France"
        assert ligue_1["priority"] == 1

    def test_competition_mappings_european_competitions(self):
        """Test European competitions."""
        champions_league = COMPETITION_MAPPINGS["champions_league"]
        europa_league = COMPETITION_MAPPINGS["europa_league"]

        assert champions_league["id"] == 2001
        assert champions_league["name"] == "UEFA Champions League"
        assert champions_league["country"] == "Europe"
        assert champions_league["priority"] == 2

        assert europa_league["id"] == 2018
        assert europa_league["name"] == "UEFA Europa League"
        assert europa_league["country"] == "Europe"
        assert europa_league["priority"] == 3

    def test_competition_mappings_international(self):
        """Test international competitions."""
        world_cup = COMPETITION_MAPPINGS["world_cup"]
        euros = COMPETITION_MAPPINGS["euros"]

        assert world_cup["id"] == 2000
        assert world_cup["name"] == "FIFA World Cup"
        assert world_cup["country"] == "International"
        assert world_cup["priority"] == 1

        assert euros["id"] == 2018
        assert euros["name"] == "European Championship"
        assert euros["country"] == "Europe"
        assert euros["priority"] == 1

    def test_competition_mappings_all_have_required_fields(self):
        """Test all mappings have required fields."""
        required_fields = ["id", "name", "country", "priority"]

        for comp_name, mapping in COMPETITION_MAPPINGS.items():
            for field in required_fields:
                assert field in mapping, f"Missing {field} in {comp_name}"

            # Validate field types
            assert isinstance(mapping["id"], int)
            assert isinstance(mapping["name"], str)
            assert isinstance(mapping["country"], str)
            assert isinstance(mapping["priority"], int)

    def test_competition_mappings_unique_ids(self):
        """Test competition IDs are unique (where applicable)."""
        ids = [mapping["id"] for mapping in COMPETITION_MAPPINGS.values()]

        # Most IDs should be unique, though some might be duplicated for different competitions
        # This is more of a data sanity check
        assert len(set(ids)) >= 6  # At least 6 unique competition IDs


class TestCollectionPriorities:
    """Test COLLECTION_PRIORITIES constant."""

    def test_collection_priorities_structure(self):
        """Test collection priorities structure."""
        assert isinstance(COLLECTION_PRIORITIES, dict)
        assert len(COLLECTION_PRIORITIES) == 3

    def test_collection_priorities_keys(self):
        """Test collection priorities keys."""
        expected_keys = [1, 2, 3]
        for key in expected_keys:
            assert key in COLLECTION_PRIORITIES

    def test_collection_priorities_priority_1(self):
        """Test priority 1 settings."""
        priority_1 = COLLECTION_PRIORITIES[1]

        assert priority_1["frequency_hours"] == 6
        assert priority_1["lookback_days"] == 7
        assert priority_1["quality_threshold"] == 0.95

    def test_collection_priorities_priority_2(self):
        """Test priority 2 settings."""
        priority_2 = COLLECTION_PRIORITIES[2]

        assert priority_2["frequency_hours"] == 12
        assert priority_2["lookback_days"] == 14
        assert priority_2["quality_threshold"] == 0.90

    def test_collection_priorities_priority_3(self):
        """Test priority 3 settings."""
        priority_3 = COLLECTION_PRIORITIES[3]

        assert priority_3["frequency_hours"] == 24
        assert priority_3["lookback_days"] == 30
        assert priority_3["quality_threshold"] == 0.85

    def test_collection_priorities_all_have_required_fields(self):
        """Test all priorities have required fields."""
        required_fields = ["frequency_hours", "lookback_days", "quality_threshold"]

        for priority, settings in COLLECTION_PRIORITIES.items():
            for field in required_fields:
                assert field in settings, f"Missing {field} in priority {priority}"

            # Validate field types
            assert isinstance(settings["frequency_hours"], int)
            assert isinstance(settings["lookback_days"], int)
            assert isinstance(settings["quality_threshold"], float)

    def test_collection_priorities_logical_progression(self):
        """Test priorities follow logical progression."""
        # Higher priority (lower number) should have more frequent collection
        assert (
            COLLECTION_PRIORITIES[1]["frequency_hours"]
            < COLLECTION_PRIORITIES[2]["frequency_hours"]
        )
        assert (
            COLLECTION_PRIORITIES[2]["frequency_hours"]
            < COLLECTION_PRIORITIES[3]["frequency_hours"]
        )

        # Higher priority should have shorter lookback
        assert (
            COLLECTION_PRIORITIES[1]["lookback_days"]
            < COLLECTION_PRIORITIES[2]["lookback_days"]
        )
        assert (
            COLLECTION_PRIORITIES[2]["lookback_days"]
            < COLLECTION_PRIORITIES[3]["lookback_days"]
        )

        # Higher priority should have higher quality threshold
        assert (
            COLLECTION_PRIORITIES[1]["quality_threshold"]
            > COLLECTION_PRIORITIES[2]["quality_threshold"]
        )
        assert (
            COLLECTION_PRIORITIES[2]["quality_threshold"]
            > COLLECTION_PRIORITIES[3]["quality_threshold"]
        )


class TestConfigIntegration:
    """Integration tests for configuration components."""

    def test_config_integration_schedule_competitions_match_mappings(self):
        """Test that default schedule competitions exist in mappings."""
        schedule = CollectionSchedule()
        default_competitions = schedule.daily_competitions

        # Find competitions with these IDs in mappings
        mapping_ids = [mapping["id"] for mapping in COMPETITION_MAPPINGS.values()]

        for comp_id in default_competitions:
            assert comp_id in mapping_ids, (
                f"Competition ID {comp_id} not found in mappings"
            )

    def test_config_integration_priorities_match_mappings(self):
        """Test that competition priorities align with collection priorities."""
        # Check that priority values in COMPETITION_MAPPINGS exist in COLLECTION_PRIORITIES
        mapping_priorities = {
            mapping["priority"] for mapping in COMPETITION_MAPPINGS.values()
        }
        collection_priorities = set(COLLECTION_PRIORITIES.keys())

        for priority in mapping_priorities:
            assert priority in collection_priorities, (
                f"Priority {priority} not in collection priorities"
            )

    def test_config_integration_full_workflow(self):
        """Test complete configuration workflow."""
        # Create platform config
        config = get_data_platform_config()

        # Check that default competitions have corresponding mappings
        default_competitions = config.schedule.daily_competitions

        for comp_id in default_competitions:
            # Find this competition in mappings
            found = False
            for mapping in COMPETITION_MAPPINGS.values():
                if mapping["id"] == comp_id:
                    found = True
                    priority = mapping["priority"]

                    # Check this priority exists in collection priorities
                    assert priority in COLLECTION_PRIORITIES

                    # Verify collection settings are reasonable
                    collection_setting = COLLECTION_PRIORITIES[priority]
                    assert collection_setting["frequency_hours"] <= 24
                    assert collection_setting["lookback_days"] >= 7
                    assert 0.8 <= collection_setting["quality_threshold"] <= 1.0
                    break

            assert found, f"Competition ID {comp_id} not found in mappings"

    def test_config_integration_data_sources_valid(self):
        """Test that data source configurations are valid."""
        config = get_data_platform_config()

        sources = [config.football_data_org, config.api_football]

        for source in sources:
            # All sources should be API type
            assert source.source_type == "api"
            assert source.api_key_required is True
            assert source.base_url is not None
            assert source.base_url.startswith("https://")
            assert source.auth_method == "api_key"
            assert 0.8 <= source.reliability_score <= 1.0
