#!/usr/bin/env python3
"""开发环境健康检查脚本"""

import subprocess
import sys
from pathlib import Path

# 颜色定义
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def check_command_exists(command: str) -> bool:
    """检查命令是否存在"""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{YELLOW}⚠️  {command} 未安装或不在PATH中, 跳过相关检查.{NC}")
        return False


def check_dependencies() -> bool:
    """检查依赖一致性"""
    print(f"\n{BLUE}1. 正在检查依赖一致性...{NC}")
    if not check_command_exists("uv"):
        return True  # 如果uv不存在, 跳过检查

    try:
        subprocess.run(
            ["uv", "pip", "check"], capture_output=True, text=True, check=True
        )
        print(f"{GREEN}✅ 依赖一致性检查通过{NC}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ 依赖冲突检测到:{NC}")
        print(e.stdout)
        return False


def check_code_quality_tools() -> bool:
    """快速检查代码质量工具是否正常工作"""
    print(f"\n{BLUE}2. 正在检查代码质量工具...{NC}")
    checks = [
        (["python", "-m", "ruff", "--version"], "Ruff检查"),
        (["python", "-m", "mypy", "--version"], "Mypy检查"),
        (["python", "-m", "bandit", "--version"], "Bandit检查"),
    ]

    all_passed = True
    for cmd, name in checks:
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"{GREEN}✅ {name}正常{NC}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{RED}❌ {name}失败或未安装{NC}")
            all_passed = False
    return all_passed


def check_pre_commit() -> bool:
    """检查pre-commit钩子是否安装"""
    print(f"\n{BLUE}3. 正在检查 pre-commit 钩子...{NC}")
    pre_commit_hook = Path(".git/hooks/pre-commit")
    if pre_commit_hook.exists():
        print(f"{GREEN}✅ pre-commit 钩子已安装{NC}")
        return True
    else:
        print(f"{YELLOW}⚠️ pre-commit 钩子未安装。请运行 'pre-commit install'{NC}")
        return False


if __name__ == "__main__":
    print(f"{BLUE}🔍 开始开发环境健康检查...{NC}")

    final_success = True
    final_success &= check_dependencies()
    final_success &= check_code_quality_tools()
    final_success &= check_pre_commit()

    print("-" * 30)
    if final_success:
        print(f"{GREEN}🎉 恭喜! 你的开发环境看起来很健康!{NC}")
        sys.exit(0)
    else:
        print(f"{RED}💥 环境检查发现问题, 请根据提示修复后再继续.{NC}")
        sys.exit(1)
