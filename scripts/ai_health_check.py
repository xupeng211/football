#!/usr/bin/env python3
"""🤖 AI工具环境健康检查 - 帮助AI工具快速了解项目状态"""

import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """快速AI环境检查"""
    print("🤖 AI工具环境检查...")
    print("=" * 40)

    # 基础信息
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"📁 路径: {Path.cwd()}")

    # 工具检查
    tools = {"uv": "现代依赖管理", "ruff": "代码格式化", "pytest": "测试框架"}
    print("\n🔧 工具状态:")

    for tool, desc in tools.items():
        try:
            subprocess.run(
                [tool, "--version"], capture_output=True, timeout=3, check=True
            )
            print(f"  ✅ {tool} ({desc})")
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"  ❌ {tool} 未安装")

    # 项目结构
    files = ["pyproject.toml", "Makefile", "README.md", "src/", "tests/"]
    print("\n📋 项目结构:")

    for file_path in files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} 缺失")

    # 保存状态到JSON
    status_file = Path("data/feedback/ai_environment_status.json")
    status_file.parent.mkdir(exist_ok=True)

    status = {
        "timestamp": "2024-12-19",
        "python_version": sys.version.split()[0],
        "project_path": str(Path.cwd()),
        "tools_available": [t for t in tools.keys() if check_tool(t)],
        "project_files_ok": [f for f in files if Path(f).exists()],
    }

    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

    print(f"\n📄 状态保存到: {status_file}")
    print("=" * 40)


def check_tool(tool: str) -> bool:
    """检查工具是否可用"""
    try:
        subprocess.run([tool, "--version"], capture_output=True, timeout=3, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


if __name__ == "__main__":
    main()
