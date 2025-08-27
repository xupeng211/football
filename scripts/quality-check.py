#!/usr/bin/env python3
"""
自动化代码质量检查脚本
用于在开发过程中快速验证代码质量,避免CI失败
"""

import os
import subprocess
import sys
from pathlib import Path


def run_check(name: str, cmd: list[str]) -> bool:
    """运行单个检查命令"""
    print(f"🔍 {name}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            check=False,
        )  # nosec B603
        if result.returncode == 0:
            print(f"✅ {name} 通过")
            return True
        else:
            print(f"❌ {name} 失败")
            if result.stdout:
                print("STDOUT:", result.stdout[:500])
            if result.stderr:
                print("STDERR:", result.stderr[:500])
            return False
    except Exception as e:
        print(f"❌ {name} 执行出错: {e}")
        return False


def main() -> None:
    """主函数"""
    print("🚀 开始代码质量检查...")
    print("=" * 50)

    # 检查虚拟环境
    if not os.environ.get("VIRTUAL_ENV"):
        print("⚠️  警告: 未检测到虚拟环境,建议先激活虚拟环境")
        print("   运行: source .venv/bin/activate")

        # 定义检查项目
    checks = [
        ("代码格式化检查", ["ruff", "format", "--check", "."]),
        ("代码规范检查", ["ruff", "check", "."]),
        ("类型检查", ["mypy", "apps/", "data_pipeline/"]),
        ("安全检查", ["bandit", "-r", ".", "-c", "pyproject.toml", "-q"]),
        ("测试运行", ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]),
    ]

    # 运行所有检查
    failed_checks = []
    passed_checks = []

    for name, cmd in checks:
        if run_check(name, cmd):
            passed_checks.append(name)
        else:
            failed_checks.append(name)
        print()

    # 输出总结
    print("=" * 50)
    print("📊 检查结果总结:")
    print(f"✅ 通过: {len(passed_checks)}")
    print(f"❌ 失败: {len(failed_checks)}")

    if passed_checks:
        print("\n🎉 通过的检查:")
        for check in passed_checks:
            print(f"  - {check}")

    if failed_checks:
        print("\n⚠️  失败的检查:")
        for check in failed_checks:
            print(f"  - {check}")
        print("\n💡 建议:")
        print("  1. 运行 'ruff check --fix .' 自动修复代码规范问题")
        print("  2. 运行 'ruff format .' 自动格式化代码")
        print("  3. 检查类型注解是否完整")
        print("  4. 确认测试用例是否需要更新")

        sys.exit(1)

    print("\n🎊 所有质量检查通过!代码可以安全提交.")


if __name__ == "__main__":
    main()
