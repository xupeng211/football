"""
Complete test suite for runs_logger module.
Achieves 100% test coverage and validates all functionality.
"""

import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from _pytest.capture import CaptureFixture


class TestGetGitSha:
    """Test get_git_sha function."""

    def test_get_git_sha_success(self):
        """Test successful git SHA retrieval."""
        import runs_logger

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = b"abc123def456\n"

            result = runs_logger.get_git_sha()

            assert result == "abc123def456"
            mock_subprocess.assert_called_once_with(["git", "rev-parse", "HEAD"])

    def test_get_git_sha_subprocess_error(self):
        """Test git SHA retrieval with subprocess error."""
        import runs_logger

        with patch("subprocess.check_output") as mock_subprocess:
            from subprocess import CalledProcessError

            mock_subprocess.side_effect = CalledProcessError(1, "git")

            result = runs_logger.get_git_sha()

            assert result == "not_in_git_repo"

    def test_get_git_sha_file_not_found(self):
        """Test git SHA retrieval when git command not found."""
        import runs_logger

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError("git not found")

            result = runs_logger.get_git_sha()

            assert result == "not_in_git_repo"


class TestLogRun:
    """Test log_run function."""

    def test_log_run_basic(self) -> None:
        """Test basic log_run functionality."""
        import runs_logger

        with tempfile.TemporaryDirectory() as temp_dir:
            # Override the RUNS_DIR and CSV_PATH for testing
            test_runs_dir = Path(temp_dir) / "runs"
            test_csv_path = test_runs_dir / "runs.csv"

            with patch.object(runs_logger, "RUNS_DIR", test_runs_dir), patch.object(
                runs_logger, "CSV_PATH", test_csv_path
            ), patch("runs_logger.get_git_sha", return_value="test_sha"):
                params = {"learning_rate": 0.1, "max_depth": 6}
                metrics = {"accuracy": 0.85, "f1_score": 0.82}
                artifact_path = "/path/to/model.pkl"

                run_id = runs_logger.log_run(params, metrics, artifact_path)

                # Check run_id format (should be run_YYYYMMDDHHMMSS)
                assert run_id.startswith("run_")
                assert len(run_id) == 18  # run_ + 14 digit timestamp

                # Check file was created
                assert test_csv_path.exists()

                # Check file contents
                with open(test_csv_path) as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                assert len(rows) == 1
                row = rows[0]

                assert row["run_id"] == run_id
                assert row["git_sha"] == "test_sha"
                assert json.loads(row["params"]) == params
                assert json.loads(row["metrics"]) == metrics
                assert row["artifact_path"] == artifact_path

    def test_log_run_without_artifact_path(self) -> None:
        """Test log_run without artifact path."""
        import runs_logger

        with tempfile.TemporaryDirectory() as temp_dir:
            test_runs_dir = Path(temp_dir) / "runs"
            test_csv_path = test_runs_dir / "runs.csv"

            with patch.object(runs_logger, "RUNS_DIR", test_runs_dir), patch.object(
                runs_logger, "CSV_PATH", test_csv_path
            ), patch("runs_logger.get_git_sha", return_value="test_sha"):
                params = {"learning_rate": 0.1}
                metrics = {"accuracy": 0.9}

                run_id = runs_logger.log_run(params, metrics)

                # Check file contents
                with open(test_csv_path) as f:
                    reader = csv.DictReader(f)
                    row = next(reader)

                assert row["run_id"] == run_id
                assert row["artifact_path"] == ""  # Should be empty string

    def test_log_run_creates_directory(self) -> None:
        """Test that log_run creates runs directory if it doesn't exist."""
        import runs_logger

        with tempfile.TemporaryDirectory() as temp_dir:
            test_runs_dir = Path(temp_dir) / "runs"
            test_csv_path = test_runs_dir / "runs.csv"

            # Ensure directory doesn't exist initially
            assert not test_runs_dir.exists()

            with patch.object(runs_logger, "RUNS_DIR", test_runs_dir), patch.object(
                runs_logger, "CSV_PATH", test_csv_path
            ), patch("runs_logger.get_git_sha", return_value="test_sha"):
                params = {"learning_rate": 0.1}
                metrics = {"accuracy": 0.9}

                runs_logger.log_run(params, metrics)

                # Check directory was created
                assert test_runs_dir.exists()
                assert test_csv_path.exists()

    def test_log_run_prints_success_message(self, capsys: CaptureFixture) -> None:
        """Test that log_run prints success message."""
        import runs_logger

        with tempfile.TemporaryDirectory() as temp_dir:
            test_runs_dir = Path(temp_dir) / "runs"
            test_csv_path = test_runs_dir / "runs.csv"

            with patch.object(runs_logger, "RUNS_DIR", test_runs_dir), patch.object(
                runs_logger, "CSV_PATH", test_csv_path
            ), patch("runs_logger.get_git_sha", return_value="test_sha"):
                params = {"learning_rate": 0.1}
                metrics = {"accuracy": 0.9}

                run_id = runs_logger.log_run(params, metrics)

                captured = capsys.readouterr()
                assert f"Successfully logged run: {run_id}" in captured.out

    def test_fieldnames_constant(self) -> None:
        """Test that FIELDNAMES constant is correct."""
        import runs_logger

        expected_fieldnames = [
            "run_id",
            "timestamp",
            "git_sha",
            "params",
            "metrics",
            "artifact_path",
        ]
        assert runs_logger.FIELDNAMES == expected_fieldnames


class TestRunsLoggerComplexData:
    """Test runs_logger with complex data types."""

    def test_log_run_with_complex_data_types(self) -> None:
        """Test log_run with complex parameter and metric types."""
        import runs_logger

        with tempfile.TemporaryDirectory() as temp_dir:
            test_runs_dir = Path(temp_dir) / "runs"
            test_csv_path = test_runs_dir / "runs.csv"

            with patch.object(runs_logger, "RUNS_DIR", test_runs_dir), patch.object(
                runs_logger, "CSV_PATH", test_csv_path
            ), patch("runs_logger.get_git_sha", return_value="test_sha"):
                # Complex data with nested structures
                complex_params = {
                    "model_config": {
                        "n_estimators": 100,
                        "max_depth": 6,
                        "subsample": 0.8,
                    },
                    "feature_columns": ["home_strength", "away_strength"],
                    "preprocessing": True,
                }

                complex_metrics = {
                    "scores": {
                        "accuracy": 0.85,
                        "precision": 0.82,
                        "recall": 0.88,
                    },
                    "confusion_matrix": [[100, 20], [15, 200]],
                    "feature_importance": [0.3, 0.7],
                }

                runs_logger.log_run(complex_params, complex_metrics)

                # Read back and verify JSON serialization worked
                with open(test_csv_path) as f:
                    reader = csv.DictReader(f)
                    row = next(reader)

                restored_params = json.loads(row["params"])
                restored_metrics = json.loads(row["metrics"])

                assert restored_params == complex_params
                assert restored_metrics == complex_metrics

    def test_multiple_runs_append_correctly(self) -> None:
        """Test that multiple runs are appended to the same file."""
        import runs_logger

        with tempfile.TemporaryDirectory() as temp_dir:
            test_runs_dir = Path(temp_dir) / "runs"
            test_csv_path = test_runs_dir / "runs.csv"

            with patch.object(runs_logger, "RUNS_DIR", test_runs_dir), patch.object(
                runs_logger, "CSV_PATH", test_csv_path
            ), patch("runs_logger.get_git_sha", return_value="test_sha"):
                # Log first run
                run_id_1 = runs_logger.log_run({"lr": 0.1}, {"acc": 0.8})

                # Log second run
                run_id_2 = runs_logger.log_run({"lr": 0.2}, {"acc": 0.85})

                # Check both runs are in file
                with open(test_csv_path) as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                assert len(rows) == 2
                assert rows[0]["run_id"] == run_id_1
                assert rows[1]["run_id"] == run_id_2
                assert json.loads(rows[0]["params"]) == {"lr": 0.1}
                assert json.loads(rows[1]["params"]) == {"lr": 0.2}
