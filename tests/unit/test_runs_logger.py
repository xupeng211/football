"""
测试 runs_logger.py 模块
"""

import csv
import json
from unittest.mock import patch

from runs_logger import FIELDNAMES, get_git_sha, log_run


class TestGetGitSha:
    """测试 get_git_sha 函数"""

    @patch("subprocess.check_output")
    def test_get_git_sha_success(self, mock_check_output):
        """测试成功获取 git SHA"""
        mock_check_output.return_value = b"abc123def456\n"

        result = get_git_sha()

        assert result == "abc123def456"
        mock_check_output.assert_called_once_with(["git", "rev-parse", "HEAD"])

    @patch("subprocess.check_output")
    def test_get_git_sha_subprocess_error(self, mock_check_output):
        """测试 subprocess 错误处理"""
        from subprocess import CalledProcessError

        mock_check_output.side_effect = CalledProcessError(1, "git")

        result = get_git_sha()

        assert result == "not_in_git_repo"

    @patch("subprocess.check_output")
    def test_get_git_sha_file_not_found(self, mock_check_output):
        """测试文件未找到错误处理"""
        mock_check_output.side_effect = FileNotFoundError()

        result = get_git_sha()

        assert result == "not_in_git_repo"


class TestLogRun:
    """测试 log_run 函数"""

    def test_log_run_basic(self, tmp_path):
        """测试基本的日志记录功能"""
        # 使用临时目录
        with patch("runs_logger.RUNS_DIR", tmp_path), patch(
            "runs_logger.CSV_PATH", tmp_path / "runs.csv"
        ), patch("runs_logger.get_git_sha", return_value="test_sha"):
            params = {"learning_rate": 0.01, "model": "xgb"}
            metrics = {"accuracy": 0.85, "loss": 0.25}
            artifact_path = "models/test_model.pkl"

            run_id = log_run(params, metrics, artifact_path)

            # 验证返回的 run_id 格式
            assert run_id.startswith("run_")
            assert len(run_id) == 18  # "run_" + 14位时间戳

            # 验证 CSV 文件创建
            csv_path = tmp_path / "runs.csv"
            assert csv_path.exists()

            # 验证 CSV 内容
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 1
                row = rows[0]

                assert row["run_id"] == run_id
                assert row["git_sha"] == "test_sha"
                assert json.loads(row["params"]) == params
                assert json.loads(row["metrics"]) == metrics
                assert row["artifact_path"] == artifact_path

    def test_log_run_without_artifact_path(self, tmp_path):
        """测试不提供 artifact_path 的情况"""
        with patch("runs_logger.RUNS_DIR", tmp_path), patch(
            "runs_logger.CSV_PATH", tmp_path / "runs.csv"
        ), patch("runs_logger.get_git_sha", return_value="test_sha"):
            params = {"model": "test"}
            metrics = {"score": 0.9}

            log_run(params, metrics)

            # 验证 CSV 内容
            csv_path = tmp_path / "runs.csv"
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                row = next(reader)

                assert row["artifact_path"] == ""

    def test_log_run_multiple_entries(self, tmp_path):
        """测试多次记录日志"""
        with patch("runs_logger.RUNS_DIR", tmp_path), patch(
            "runs_logger.CSV_PATH", tmp_path / "runs.csv"
        ), patch("runs_logger.get_git_sha", return_value="test_sha"):
            # 第一次记录
            run_id1 = log_run({"param1": 1}, {"metric1": 0.8})

            # 第二次记录
            run_id2 = log_run({"param2": 2}, {"metric2": 0.9})

            # 验证两次记录都存在
            csv_path = tmp_path / "runs.csv"
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 2
                assert rows[0]["run_id"] == run_id1
                assert rows[1]["run_id"] == run_id2

    def test_log_run_creates_directory(self, tmp_path):
        """测试自动创建目录"""
        runs_dir = tmp_path / "new_runs_dir"

        with patch("runs_logger.RUNS_DIR", runs_dir), patch(
            "runs_logger.CSV_PATH", runs_dir / "runs.csv"
        ), patch("runs_logger.get_git_sha", return_value="test_sha"):
            assert not runs_dir.exists()

            log_run({"test": 1}, {"test": 0.5})

            assert runs_dir.exists()
            assert (runs_dir / "runs.csv").exists()

    def test_fieldnames_constant(self):
        """测试 FIELDNAMES 常量"""
        expected_fields = [
            "run_id",
            "timestamp",
            "git_sha",
            "params",
            "metrics",
            "artifact_path",
        ]
        assert FIELDNAMES == expected_fields

    @patch("builtins.print")
    def test_log_run_prints_success_message(self, mock_print, tmp_path):
        """测试成功消息打印"""
        with patch("runs_logger.RUNS_DIR", tmp_path), patch(
            "runs_logger.CSV_PATH", tmp_path / "runs.csv"
        ), patch("runs_logger.get_git_sha", return_value="test_sha"):
            run_id = log_run({"test": 1}, {"test": 0.5})

            mock_print.assert_called_once_with(f"Successfully logged run: {run_id}")
