#!/usr/bin/env python3
"""🤖 AI文件实时监控器 - 监控文件操作并提供实时指导"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path


class AIFileMonitor:
    """AI文件操作实时监控器"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.guard_script = self.project_root / "scripts" / "ai_file_guard.py"
        self.status_file = (
            self.project_root / "data" / "feedback" / "ai_file_status.json"
        )
        self.monitored_extensions = {".py", ".json", ".yaml", ".toml"}

    def scan_recent_files(self, minutes: int = 5) -> set[str]:
        """扫描最近修改的文件"""
        cutoff_time = time.time() - (minutes * 60)
        recent_files = set()

        for root, dirs, files in os.walk(self.project_root):
            # 跳过不需要的目录
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d not in ["__pycache__", "node_modules"]
            ]

            for file in files:
                file_path = Path(root) / file
                if (
                    file_path.suffix in self.monitored_extensions
                    and file_path.stat().st_mtime > cutoff_time
                ):
                    recent_files.add(str(file_path))

        return recent_files

    def check_file_with_guard(self, file_path: str) -> dict:
        """使用守护程序检查文件"""
        try:
            result = subprocess.run(
                [sys.executable, str(self.guard_script), file_path],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            return {
                "file": file_path,
                "exit_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr,
                "timestamp": time.time(),
            }
        except subprocess.TimeoutExpired:
            return {
                "file": file_path,
                "exit_code": -1,
                "output": "",
                "error": "检查超时",
                "timestamp": time.time(),
            }

    def save_status(self, checks: list) -> None:
        """保存检查状态"""
        self.status_file.parent.mkdir(parents=True, exist_ok=True)

        status = {
            "last_scan": time.time(),
            "checks": checks,
            "summary": {
                "total_files": len(checks),
                "warnings": sum(1 for c in checks if "警告" in c.get("output", "")),
                "errors": sum(1 for c in checks if c.get("exit_code", 0) != 0),
            },
        }

        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)

    def run_scan(self, minutes: int = 5) -> None:
        """运行文件扫描"""
        print(f"🔍 扫描最近 {minutes} 分钟的文件变化...")

        recent_files = self.scan_recent_files(minutes)

        if not recent_files:
            print("✅ 没有发现最近修改的文件")
            return

        print(f"📁 发现 {len(recent_files)} 个最近修改的文件")

        checks = []
        for file_path in recent_files:
            print(f"🔍 检查: {file_path}")
            check_result = self.check_file_with_guard(file_path)
            checks.append(check_result)

            # 显示警告
            if "警告" in check_result.get("output", ""):
                print(f"⚠️  {file_path} 有潜在问题")

        self.save_status(checks)
        print(f"📊 检查完成, 状态保存到: {self.status_file}")

    def show_status(self) -> None:
        """显示当前状态"""
        if not self.status_file.exists():
            print("📊 暂无状态数据, 请先运行扫描")
            return

        with open(self.status_file, encoding="utf-8") as f:
            status = json.load(f)

        summary = status.get("summary", {})
        print("📊 AI文件监控状态:")
        print(f"  📁 总文件数: {summary.get('total_files', 0)}")
        print(f"  ⚠️  警告数: {summary.get('warnings', 0)}")
        print(f"  ❌ 错误数: {summary.get('errors', 0)}")

        last_scan = status.get("last_scan", 0)
        if last_scan:
            scan_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_scan))
            print(f"  🕐 最后扫描: {scan_time}")


def main():
    """命令行工具"""
    monitor = AIFileMonitor()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python ai_file_monitor.py scan [minutes]  # 扫描最近修改的文件")
        print("  python ai_file_monitor.py status         # 显示状态")
        sys.exit(1)

    command = sys.argv[1]

    if command == "scan":
        minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        monitor.run_scan(minutes)
    elif command == "status":
        monitor.show_status()
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
