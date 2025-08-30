import pytest
from hypothesis import given
from hypothesis import strategies as st

from data_pipeline.features.build import create_feature_vector

# Strategy for generating valid team names (non-empty strings)
valid_team_names = st.text(min_size=1, max_size=50).filter(lambda s: s.strip() != "")

# Strategy for generating valid odds (floats between 1.01 and 100.0)
valid_odds = st.floats(
    min_value=1.01, max_value=100.0, allow_nan=False, allow_infinity=False
)

# Strategy for generating a wide range of invalid odds values
invalid_odds = st.one_of(
    st.floats(max_value=0, allow_nan=False, allow_infinity=False),  # Zero or negative
    st.just(float("nan")),
    st.just(float("inf")),
    st.just(float("-inf")),
    st.text(),  # Not a number
)

# Strategy for generating a wide range of invalid team names
invalid_team_names = st.one_of(
    st.just(""),  # Empty string
    st.just("   "),  # Whitespace only
    st.text(min_size=101),  # Too long
    st.integers(),  # Not a string
    st.booleans(),  # Not a string
)


@given(
    home_team=valid_team_names,
    away_team=valid_team_names,
    odds_h=valid_odds,
    odds_d=valid_odds,
    odds_a=valid_odds,
)
def test_create_feature_vector_with_valid_inputs(
    home_team, away_team, odds_h, odds_d, odds_a
):
    """
    Property: The function must not raise an error with valid inputs.
    """
    try:
        features = create_feature_vector(home_team, away_team, odds_h, odds_d, odds_a)
        assert isinstance(features, dict)
        assert "prob_h_norm" in features
    except ValueError as e:
        pytest.fail(
            f"create_feature_vector raised an unexpected ValueError with valid inputs: {e}"
        )


@given(
    home_team=invalid_team_names,
    away_team=valid_team_names,
    odds_h=valid_odds,
    odds_d=valid_odds,
    odds_a=valid_odds,
)
def test_create_feature_vector_raises_on_invalid_home_team(
    home_team, away_team, odds_h, odds_d, odds_a
):
    """
    Property: The function must raise a ValueError for invalid home_team names.
    """
    with pytest.raises(ValueError):
        create_feature_vector(home_team, away_team, odds_h, odds_d, odds_a)


@given(
    home_team=valid_team_names,
    away_team=valid_team_names,
    odds_h=invalid_odds,
    odds_d=valid_odds,
    odds_a=valid_odds,
)
def test_create_feature_vector_raises_on_invalid_odds(
    home_team, away_team, odds_h, odds_d, odds_a
):
    """
    Property: The function must raise a ValueError for invalid odds.
    """
    with pytest.raises(ValueError):
        create_feature_vector(home_team, away_team, odds_h, odds_d, odds_a)
