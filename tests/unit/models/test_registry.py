"""
Unit tests for the ModelRegistry.
"""

from datetime import datetime
from pathlib import Path

import pytest

from models.registry import ModelMetadata, ModelRegistry


@pytest.fixture
def registry(tmp_path: Path) -> ModelRegistry:
    """Provides a ModelRegistry instance with a temporary path."""
    return ModelRegistry(registry_path=str(tmp_path))


@pytest.fixture
def sample_metadata() -> ModelMetadata:
    """Provides a sample ModelMetadata instance."""
    return ModelMetadata(
        model_id="test_model",
        version="1.0.0",
        name="Test Model",
        description="A model for testing.",
        framework="xgboost",
        accuracy=0.9,
        precision=0.8,
        recall=0.7,
        f1_score=0.75,
        training_date=datetime.now(),
        training_duration=120.5,
        training_samples=1000,
        feature_count=10,
        model_path="",
        metadata_path="",
    )


def test_registry_initialization(registry: ModelRegistry):
    """Tests that the registry initializes correctly."""
    assert registry.index_file.exists()
    assert "models" in registry.index
    assert "active_versions" in registry.index


def test_register_and_load_model(
    registry: ModelRegistry, sample_metadata: ModelMetadata
):
    """Tests registering a new model and loading it back."""
    model_to_save = {"key": "value"}

    # Register
    registry.register_model(model_to_save, sample_metadata, make_active=True)

    # Verify index
    assert "test_model" in registry.index["models"]
    assert registry.index["active_versions"]["test_model"] == "1.0.0"

    # Load active version
    loaded_model = registry.load_model("test_model")
    assert loaded_model == model_to_save

    # Load specific version
    loaded_model_versioned = registry.load_model("test_model", "1.0.0")
    assert loaded_model_versioned == model_to_save


def test_promote_model(registry: ModelRegistry, sample_metadata: ModelMetadata):
    """Tests promoting a model version."""
    model_to_save = {"key": "value"}
    sample_metadata.version = "1.0.0"
    registry.register_model(model_to_save, sample_metadata, make_active=False)

    sample_metadata.version = "2.0.0"
    registry.register_model(model_to_save, sample_metadata, make_active=True)

    assert registry.get_active_version("test_model") == "2.0.0"

    registry.promote_model("test_model", "1.0.0")
    assert registry.get_active_version("test_model") == "1.0.0"
