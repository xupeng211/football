# tests/unit/apps/api/test_model_registry.py

from unittest.mock import patch

from apps.api.model_registry import check_model_registry


class TestCheckModelRegistry:
    """Tests for the check_model_registry function."""

    @patch("apps.api.model_registry.prediction_service")
    def test_check_model_registry_success(self, mock_prediction_service, monkeypatch):
        """Test the model registry check succeeds when models are available."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_prediction_service.list_models.return_value = [
            "model_v1.pkl",
            "model_v2.pkl",
        ]

        is_ok, message = check_model_registry()

        assert is_ok is True
        assert "Latest model 'model_v2.pkl' loaded" in message
        mock_prediction_service.list_models.assert_called_once()
        mock_prediction_service.load_model.assert_called_once_with("model_v2.pkl")

    @patch("apps.api.model_registry.prediction_service")
    def test_check_model_registry_no_models(self, mock_prediction_service, monkeypatch):
        """Test the check fails when no models are found in the registry."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_prediction_service.list_models.return_value = []

        is_ok, message = check_model_registry()

        assert is_ok is False
        assert "No models found in the registry" in message
        mock_prediction_service.list_models.assert_called_once()
        mock_prediction_service.load_model.assert_not_called()

    @patch("apps.api.model_registry.prediction_service")
    def test_check_model_registry_exception_on_list(
        self, mock_prediction_service, monkeypatch
    ):
        """Test the check fails when listing models raises an exception."""
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        mock_prediction_service.list_models.side_effect = Exception("Connection failed")

        is_ok, message = check_model_registry()

        assert is_ok is False
        assert "Model registry check failed: Connection failed" in message

    def test_check_model_registry_skipped_in_test_env(self, monkeypatch):
        """Test that the check is skipped when PYTEST_CURRENT_TEST is set."""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")

        is_ok, message = check_model_registry()

        assert is_ok is True
        assert "Model registry check skipped in test environment" in message
