# data_pipeline/contract_validator.py

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

CONTRACT_PATH = Path(__file__).parent.parent / "contracts" / "feature_specs.yaml"


def load_contract() -> Any:
    """Loads the feature contract from the YAML file."""
    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(f"Feature contract not found at {CONTRACT_PATH}")
    with open(CONTRACT_PATH) as f:
        contract = yaml.safe_load(f)
    return contract


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validates a DataFrame against the feature contract.

    Args:
        df (pd.DataFrame): The DataFrame to validate.

    Returns:
        bool: True if the DataFrame is valid, False otherwise.
        list: A list of validation errors.
    """
    contract = load_contract()
    errors = []

    # Check for missing columns
    contract_features = {feature["name"] for feature in contract["features"]}
    df_columns = set(df.columns)
    missing_columns = contract_features - df_columns
    if missing_columns:
        errors.append(f"Missing columns in DataFrame: {missing_columns}")

    # Check data types
    for feature in contract["features"]:
        name = feature["name"]
        expected_dtype = feature["dtype"]
        if name in df.columns:
            actual_dtype = str(df[name].dtype)
            if actual_dtype != expected_dtype:
                errors.append(
                    f"Invalid dtype for column '{name}': "
                    f"expected '{expected_dtype}', got '{actual_dtype}'"
                )

    is_valid = not errors
    return is_valid, errors


if __name__ == "__main__":
    # Example usage and self-test
    try:
        # Create a sample valid DataFrame
        valid_data = {
            "home_team_goal_avg_l30d": [1.5, 2.1],
            "away_team_goal_avg_l30d": [1.2, 0.8],
            "home_team_conceded_avg_l30d": [0.9, 1.3],
            "away_team_conceded_avg_l30d": [1.1, 1.5],
            "home_team_win_rate_l10g": [0.6, 0.7],
            "away_team_win_rate_l10g": [0.5, 0.4],
            "odds_h": [2.5, 2.3],
            "odds_d": [3.2, 3.4],
            "odds_a": [2.8, 3.0],
            "league_id": [1, 2],
        }
        valid_df = pd.DataFrame(valid_data)
        for col, dtype in valid_df.dtypes.items():
            if "int" in str(dtype):
                valid_df[col] = valid_df[col].astype("int64")
            if "float" in str(dtype):
                valid_df[col] = valid_df[col].astype("float64")

        is_valid, errors = validate_dataframe(valid_df)
        print("Validation result for valid DataFrame:", is_valid)
        assert is_valid, f"Valid DataFrame failed validation: {errors}"

        # Create a sample invalid DataFrame (missing column and wrong dtype)
        invalid_data = valid_data.copy()
        del invalid_data["odds_a"]
        invalid_df = pd.DataFrame(invalid_data)
        invalid_df["league_id"] = invalid_df["league_id"].astype("float64")

        is_valid, errors = validate_dataframe(invalid_df)
        print("\nValidation result for invalid DataFrame:", is_valid)
        print("Errors:", errors)
        assert not is_valid, "Invalid DataFrame passed validation"
        assert len(errors) == 2, "Expected two validation errors"

        print("\nContract validator self-test passed!")

    except Exception as e:
        print(f"An error occurred during self-test: {e}")
