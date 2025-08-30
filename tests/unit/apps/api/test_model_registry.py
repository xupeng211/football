# tests/unit/apps/api/test_model_registry.py

from unittest.mock import patch

from apps.api.model_registry import check_model_registry


class TestCheckModelRegistry:
    """Tests for the check_model_registry function."""

    @patch("apps.api.model_registry.prediction_service")
    def test_check_model_registry_success(self, mock_prediction_service, monkeypatch):
        """Test the model registry check succeeds when a valid model is loaded."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_prediction_service.get_model_version.return_value = "model_v2.pkl"

        is_ok, message = check_model_registry()

        assert is_ok is True
        assert message == "Model 'model_v2.pkl' is loaded and healthy."
        mock_prediction_service.get_model_version.assert_called_once()

    @patch("apps.api.model_registry.prediction_service")
    def test_check_model_registry_no_model_loaded(
        self, mock_prediction_service, monkeypatch
    ):
        """Test the check fails when no model is loaded."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_prediction_service.get_model_version.return_value = None

        is_ok, message = check_model_registry()

        assert is_ok is False
        assert message == "No model is loaded in the prediction service."
        mock_prediction_service.get_model_version.assert_called_once()

    @patch("apps.api.model_registry.prediction_service")
    def test_check_model_registry_stub_model_loaded(
        self, mock_prediction_service, monkeypatch
    ):
        """Test the check fails when a stub model is loaded."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_prediction_service.get_model_version.return_value = "stub_model_v1"

        is_ok, message = check_model_registry()

        assert is_ok is False
        assert message == "A stub model ('stub_model_v1') is loaded."
        mock_prediction_service.get_model_version.assert_called_once()

    @patch("apps.api.model_registry.prediction_service")
    def test_check_model_registry_exception(self, mock_prediction_service, monkeypatch):
        """Test the check fails when get_model_version raises an exception."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_prediction_service.get_model_version.side_effect = Exception(
            "Connection failed"
        )

        is_ok, message = check_model_registry()

        assert is_ok is False
        assert (
            "Model registry check failed with an exception: Connection failed"
            in message
        )
        mock_prediction_service.get_model_version.assert_called_once()

    def test_check_model_registry_skipped_in_test_env(self, monkeypatch):
        """Test that the check is skipped when PYTEST_CURRENT_TEST is set."""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")

        is_ok, message = check_model_registry()

        assert is_ok is True
        assert "Model registry check skipped in test environment" in message
