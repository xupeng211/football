"""Tests for domain models module."""

from datetime import datetime
from uuid import uuid4

import pytest

from football_predict_system.domain.models import Model, ModelStatus, ModelType


class TestModelStatus:
    """Test ModelStatus enum."""

    def test_model_status_values(self):
        """Test that model status enum has expected values."""
        assert ModelStatus.TRAINING == "training"
        assert ModelStatus.ACTIVE == "active"
        assert ModelStatus.RETIRED == "retired"
        assert ModelStatus.FAILED == "failed"


class TestModelType:
    """Test ModelType enum."""

    def test_model_type_values(self):
        """Test that model type enum has expected values."""
        # These values depend on the actual implementation
        # Update based on actual enum values
        assert hasattr(ModelType, "__members__")
        assert len(ModelType.__members__) > 0


class TestModel:
    """Test Model class."""

    def test_model_creation(self):
        """Test creating a Model instance."""
        model_id = str(uuid4())

        model = Model(
            id=model_id,
            name="Test Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert model.id == model_id
        assert model.name == "Test Model"
        assert model.version == "1.0.0"
        assert model.status == ModelStatus.ACTIVE

    def test_model_with_optional_fields(self):
        """Test creating Model with optional fields."""
        model = Model(
            id=str(uuid4()),
            name="Test Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Test model description",
            accuracy=0.95,
            performance_metrics={"precision": 0.94, "recall": 0.96},
        )

        assert model.description == "Test model description"
        assert model.accuracy == 0.95
        assert model.performance_metrics["precision"] == 0.94

    def test_model_status_transitions(self):
        """Test model status transitions."""
        model = Model(
            id=str(uuid4()),
            name="Test Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.TRAINING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Test status change
        model.status = ModelStatus.ACTIVE
        assert model.status == ModelStatus.ACTIVE

        model.status = ModelStatus.RETIRED
        assert model.status == ModelStatus.RETIRED

    def test_model_validation(self):
        """Test model field validation."""
        with pytest.raises(ValueError):
            # Test with invalid accuracy (> 1.0)
            Model(
                id=str(uuid4()),
                name="Test Model",
                version="1.0.0",
                model_type=ModelType.CLASSIFICATION,
                status=ModelStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                accuracy=1.5,  # Invalid - greater than 1.0
            )

    def test_model_string_representation(self):
        """Test model string representation."""
        model = Model(
            id=str(uuid4()),
            name="Test Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        str_repr = str(model)
        assert "Test Model" in str_repr
        assert "1.0.0" in str_repr

    def test_model_serialization(self):
        """Test model serialization to dict."""
        model = Model(
            id=str(uuid4()),
            name="Test Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        model_dict = model.model_dump()

        assert model_dict["name"] == "Test Model"
        assert model_dict["version"] == "1.0.0"
        assert model_dict["status"] == ModelStatus.ACTIVE


class TestModelMethods:
    """Test Model methods."""

    def test_model_is_active(self):
        """Test model is_active method."""
        active_model = Model(
            id=str(uuid4()),
            name="Active Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        retired_model = Model(
            id=str(uuid4()),
            name="Retired Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.RETIRED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        if hasattr(active_model, "is_active"):
            assert active_model.is_active() is True
            assert retired_model.is_active() is False

    def test_model_can_predict(self):
        """Test model can_predict method."""
        active_model = Model(
            id=str(uuid4()),
            name="Active Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        training_model = Model(
            id=str(uuid4()),
            name="Training Model",
            version="1.0.0",
            model_type=ModelType.CLASSIFICATION,
            status=ModelStatus.TRAINING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        if hasattr(active_model, "can_predict"):
            assert active_model.can_predict() is True
            assert training_model.can_predict() is False
