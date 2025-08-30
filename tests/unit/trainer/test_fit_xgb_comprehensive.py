from unittest.mock import MagicMock, patch

import pandas as pd


def test_fit_xgb_main_function():
    """
    Test the main function of fit_xgb module with proper mocking.
    """
    # Mock all external dependencies
    with patch("trainer.fit_xgb.setup_logging"), patch(
        "trainer.fit_xgb.load_data_from_db"
    ) as mock_load_data, patch(
        "trainer.fit_xgb.train_xgboost_model"
    ) as mock_train_model, patch(
        "trainer.fit_xgb.evaluate_model"
    ) as mock_evaluate_model, patch(
        "trainer.fit_xgb.save_model_and_metrics"
    ) as mock_save_model:
        # Setup mock return values with enough samples for stratified split
        mock_features_df = pd.DataFrame(
            {
                "match_id": list(range(1, 21)),
                "feature1": [float(i) for i in range(1, 21)],
                "feature2": [float(i) * 0.5 for i in range(1, 21)],
                "target": [
                    i % 3 for i in range(20)
                ],  # Balanced classes: 0,1,2,0,1,2...
            }
        )
        mock_load_data.return_value = mock_features_df

        mock_model = MagicMock()
        mock_train_model.return_value = mock_model

        mock_metrics = {"accuracy": 0.85, "log_loss": 0.45, "roc_auc": 0.78}
        mock_evaluate_model.return_value = mock_metrics

        mock_save_model.return_value = "xgb_20231201_120000"

        # Import and call main function
        from trainer.fit_xgb import main

        main()

        # Verify function calls
        mock_load_data.assert_called_once()
        mock_train_model.assert_called_once()
        mock_evaluate_model.assert_called_once()
        mock_save_model.assert_called_once()
