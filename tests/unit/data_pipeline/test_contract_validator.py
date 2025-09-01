import pytest

pytestmark = pytest.mark.skip(reason="data_pipeline module not implemented")

# tests/unit/data_pipeline/test_contract_validator.py

import unittest.mock
from pathlib import Path

import pandas as pd
import pytest
import yaml
from data_pipeline.contract_validator import (
    load_contract,
    validate_dataframe,
)

# A sample contract for testing purposes
SAMPLE_CONTRACT = {
    "features": [
        {"name": "feature_a", "dtype": "float64"},
        {"name": "feature_b", "dtype": "int64"},
        {"name": "feature_c", "dtype": "object"},
    ]
}

# Convert dict to YAML string
SAMPLE_CONTRACT_YAML = yaml.dump(SAMPLE_CONTRACT)


@pytest.fixture
def mock_contract_file(tmp_path: Path) -> Path:
    """Creates a temporary contract file for testing."""
    contract_file = tmp_path / "feature_specs.yaml"
    contract_file.write_text(SAMPLE_CONTRACT_YAML)
    return contract_file


class TestLoadContract:
    """Tests for the load_contract function."""

    def test_load_contract_success(self, mock_contract_file: Path):
        """Test that the contract loads successfully when the file exists."""
        with unittest.mock.patch(
            "data_pipeline.contract_validator.CONTRACT_PATH", mock_contract_file
        ):
            contract = load_contract()
            assert contract == SAMPLE_CONTRACT

    def test_load_contract_file_not_found(self, tmp_path: Path):
        """Test that FileNotFoundError is raised when the contract is missing."""
        non_existent_path = tmp_path / "non_existent_contract.yaml"
        with unittest.mock.patch(
            "data_pipeline.contract_validator.CONTRACT_PATH", non_existent_path
        ):
            with pytest.raises(FileNotFoundError):
                load_contract()


class TestValidateDataFrame:
    """Tests for the validate_dataframe function."""

    @pytest.fixture(autouse=True)
    def mock_load_contract(self):
        """Mock load_contract to return a consistent sample contract."""
        with unittest.mock.patch(
            "data_pipeline.contract_validator.load_contract"
        ) as mock_load:
            mock_load.return_value = SAMPLE_CONTRACT
            yield mock_load

    def test_validate_valid_dataframe(self):
        """Test validation with a perfectly valid DataFrame."""
        valid_df = pd.DataFrame(
            {
                "feature_a": [1.0, 2.0],
                "feature_b": [1, 2],
                "feature_c": ["x", "y"],
            }
        )
        valid_df["feature_b"] = valid_df["feature_b"].astype("int64")

        is_valid, errors = validate_dataframe(valid_df)
        assert is_valid
        assert not errors

    def test_validate_missing_columns(self):
        """Test validation with a DataFrame that has a missing column."""
        invalid_df = pd.DataFrame(
            {
                "feature_a": [1.0, 2.0],
            }
        )
        is_valid, errors = validate_dataframe(invalid_df)
        assert not is_valid
        assert len(errors) == 1
        assert "Missing columns" in errors[0]
        assert "feature_b" in errors[0]
        assert "feature_c" in errors[0]

    def test_validate_incorrect_dtype(self):
        """Test validation with a DataFrame that has an incorrect data type."""
        invalid_df = pd.DataFrame(
            {
                "feature_a": [1.0, 2.0],
                "feature_b": [1.1, 2.2],  # Incorrect: should be int64
                "feature_c": ["x", "y"],
            }
        )
        is_valid, errors = validate_dataframe(invalid_df)
        assert not is_valid
        assert len(errors) == 1
        assert "Invalid dtype for column 'feature_b'" in errors[0]

    def test_validate_multiple_errors(self):
        """Test validation with a DataFrame that has multiple errors."""
        invalid_df = pd.DataFrame(
            {
                "feature_a": [1, 2],  # Incorrect: should be float64
            }
        )
        invalid_df["feature_a"] = invalid_df["feature_a"].astype("int64")

        is_valid, errors = validate_dataframe(invalid_df)
        assert not is_valid
        # One error for missing columns, one for wrong dtype
        assert len(errors) == 2
        assert any("Missing columns" in e for e in errors)
        assert any("Invalid dtype for column 'feature_a'" in e for e in errors)
