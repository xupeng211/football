# runs_logger.py

import csv
import datetime
import json
import subprocess
from pathlib import Path

RUNS_DIR = Path(__file__).parent / "runs"
CSV_PATH = RUNS_DIR / "runs.csv"
FIELDNAMES = ["run_id", "timestamp", "git_sha", "params", "metrics", "artifact_path"]


def get_git_sha() -> str:
    """Gets the current git commit SHA."""
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .strip()
            .decode("utf-8")
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "not_in_git_repo"


def log_run(params: dict, metrics: dict, artifact_path: str | None = None) -> str:
    """
    Logs a new experiment run to the CSV file.

    Args:
        params (dict): A dictionary of training parameters.
        metrics (dict): A dictionary of performance metrics.
        artifact_path (str | None): The path to the saved model artifact.

    Returns:
        str: The ID of the logged run.
    """
    RUNS_DIR.mkdir(exist_ok=True)

    # Create unique run ID
    timestamp_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    run_id = f"run_{timestamp_id}"

    # Prepare data for CSV
    log_entry = {
        "run_id": run_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_sha": get_git_sha(),
        "params": json.dumps(params),
        "metrics": json.dumps(metrics),
        "artifact_path": artifact_path or "",
    }

    # Write to CSV
    file_exists = CSV_PATH.is_file()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)

    print(f"Successfully logged run: {run_id}")
    return run_id


if __name__ == "__main__":
    # Example usage and self-test
    print("Running self-test for runs_logger...")

    # Define sample data
    sample_params = {
        "learning_rate": 0.01,
        "n_estimators": 100,
        "model_type": "xgboost",
    }
    sample_metrics = {"accuracy": 0.85, "roc_auc": 0.92, "loss": 0.25}
    sample_artifact_path = "models/artifacts/model_20250828.pkl"

    # Log the run
    logged_run_id = log_run(
        params=sample_params, metrics=sample_metrics, artifact_path=sample_artifact_path
    )

    # Verify the log entry
    assert CSV_PATH.is_file(), "CSV file was not created."

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0, "No data was written to the CSV."
        last_row = rows[-1]
        assert last_row["run_id"] == logged_run_id
        assert last_row["git_sha"] != ""
        assert json.loads(last_row["params"]) == sample_params
        assert json.loads(last_row["metrics"]) == sample_metrics
        assert last_row["artifact_path"] == sample_artifact_path

    print(f"Self-test passed. Log is available at {CSV_PATH}")
