# tests/evaluation/test_data_leakage_guard.py

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


@pytest.fixture
def create_test_data():
    """Creates a sample DataFrame for testing data leakage."""
    # Generate synthetic data that has a clear time dependency
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=200, freq="D"))
    # Feature that is highly correlated with the target, but with a time lag
    feature1 = np.sin(np.arange(200) / 20) + np.random.normal(0, 0.1, 200)
    # A noisy feature
    feature2 = np.random.rand(200)
    # Target variable that depends on the future value of feature1
    target = (np.roll(feature1, -5) > 0.5).astype(int)

    df = pd.DataFrame(
        {"date": dates, "feature1": feature1, "feature2": feature2, "target": target}
    )
    return df


def train_model(X_train, y_train):
    """Trains a simple RandomForestClassifier."""
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)
    return model


def test_time_window_dislocation(create_test_data):
    """Tests for data leakage by dislocating the time window.

    This test checks if a model trained on data where the features and target
    are misaligned in time performs significantly worse than a model trained
    on correctly aligned data.
    """
    df = create_test_data
    X = df[["feature1", "feature2"]]
    y = df["target"]

    # Correctly aligned data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, shuffle=False
    )
    model_aligned = train_model(X_train, y_train)
    auc_aligned = roc_auc_score(y_test, model_aligned.predict_proba(X_test)[:, 1])

    # Introduce a time dislocation by shifting the features
    X_dislocated = X.shift(10).fillna(0)
    X_train_dis, X_test_dis, y_train_dis, y_test_dis = train_test_split(
        X_dislocated, y, test_size=0.3, random_state=42, shuffle=False
    )
    model_dislocated = train_model(X_train_dis, y_train_dis)
    auc_dislocated = roc_auc_score(
        y_test_dis, model_dislocated.predict_proba(X_test_dis)[:, 1]
    )

    # The model with dislocated data should perform significantly worse
    assert auc_aligned > 0.7, "Model with aligned data should have good performance"
    assert auc_dislocated < 0.6, "Model with dislocated data should perform poorly"
    assert (
        auc_aligned > auc_dislocated + 0.2
    ), "Significant performance drop expected with dislocation"


def test_label_randomization(create_test_data):
    """Tests for data leakage by randomizing the labels.

    If the model can still achieve high performance after the labels have been
    randomized, it suggests that there is data leakage from the features to the labels.
    """
    df = create_test_data
    X = df[["feature1", "feature2"]]
    y = df["target"]

    # Train on original labels
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    model_original = train_model(X_train, y_train)
    auc_original = roc_auc_score(y_test, model_original.predict_proba(X_test)[:, 1])

    # Train on randomized labels
    y_randomized = y.sample(frac=1, random_state=42).reset_index(drop=True)
    X_train_rand, X_test_rand, y_train_rand, y_test_rand = train_test_split(
        X, y_randomized, test_size=0.3, random_state=42
    )
    model_randomized = train_model(X_train_rand, y_train_rand)
    auc_randomized = roc_auc_score(
        y_test_rand, model_randomized.predict_proba(X_test_rand)[:, 1]
    )

    # The randomized model's performance should be close to random (AUC ~ 0.5)
    assert auc_original > 0.7, "Model with original labels should have good performance"
    assert (
        abs(auc_randomized - 0.5) < 0.15
    ), "Randomized label model AUC should be close to 0.5"
