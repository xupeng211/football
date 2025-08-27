#!/usr/bin/env python3
"""
测试运行脚本
支持分层次运行不同类型的测试
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """测试运行器"""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.test_dirs = {
            "unit": "tests/unit",
            "integration": "tests/integration",
            "regression": "tests/regression",
            "e2e": "tests/e2e",
            "all": "tests/",
        }

    def run_tests(
        self,
        test_type: str = "all",
        coverage: bool = True,
        verbose: bool = True,
        parallel: bool = False,
        markers: Optional[List[str]] = None,
    ) -> int:
        """运行指定类型的测试"""

        if test_type not in self.test_dirs:
            print(f"❌ 无效的测试类型: {test_type}")
            print(f"可用类型: {list(self.test_dirs.keys())}")
            return 1

        test_path = self.test_dirs[test_type]

        # 构建pytest命令
        cmd = ["python", "-m", "pytest"]

        # 添加测试路径
        cmd.append(test_path)

        # 添加选项
        if verbose:
            cmd.append("-v")

        if coverage and test_type in ["all", "unit"]:
            cmd.extend(
                [
                    "--cov=.",
                    "--cov-report=term-missing",
                    "--cov-report=html:htmlcov",
                    "--cov-report=xml:coverage.xml",
                ]
            )

        if parallel:
            cmd.extend(["-n", "auto"])

        # 添加标记过滤
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        # 添加其他选项
        cmd.extend(["--tb=short", "--strict-markers"])

        print(f"🚀 运行 {test_type} 测试...")
        print(f"📝 命令: {' '.join(cmd)}")
        print(f"📁 工作目录: {self.project_root}")

        start_time = time.time()

        # 运行测试
        result = subprocess.run(cmd, cwd=self.project_root)

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n⏱️ 测试运行时间: {duration:.2f} 秒")

        if result.returncode == 0:
            print(f"✅ {test_type} 测试全部通过!")
        else:
            print(f"❌ {test_type} 测试失败!")

        return result.returncode

    def run_quick_tests(self) -> int:
        """运行快速测试套件"""
        print("🏃 运行快速测试套件...")
        return self.run_tests("unit", coverage=False)

    def run_full_tests(self) -> int:
        """运行完整测试套件"""
        print("🔄 运行完整测试套件...")

        test_sequence = [
            ("unit", "单元测试"),
            ("integration", "集成测试"),
            ("regression", "回归测试"),
            ("e2e", "端到端测试"),
        ]

        overall_result = 0
        results = {}

        for test_type, description in test_sequence:
            print(f"\n{'='*50}")
            print(f"🎯 开始 {description}")
            print(f"{'='*50}")

            result = self.run_tests(test_type, coverage=(test_type == "unit"))
            results[test_type] = result

            if result != 0:
                print(f"❌ {description} 失败,停止后续测试")
                overall_result = result
                break

        # 输出总结
        print(f"\n{'='*50}")
        print("📊 测试结果总结")
        print(f"{'='*50}")

        for test_type, description in test_sequence:
            if test_type in results:
                status = "✅ 通过" if results[test_type] == 0 else "❌ 失败"
                print(f"{description}: {status}")
            else:
                print(f"{description}: ⏭️ 跳过")

        return overall_result

    def run_ci_tests(self) -> int:
        """运行CI环境的测试"""
        print("🤖 运行CI测试套件...")

        # CI环境通常运行核心测试,跳过耗时的端到端测试
        ci_sequence = [
            ("unit", "单元测试"),
            ("integration", "集成测试"),
            ("regression", "回归测试"),
        ]

        for test_type, description in ci_sequence:
            print(f"\n🎯 CI: {description}")
            result = self.run_tests(
                test_type, coverage=(test_type == "unit"), parallel=True
            )

            if result != 0:
                print(f"❌ CI: {description} 失败")
                return result

        print("✅ CI: 所有测试通过")
        return 0

    def run_smoke_tests(self) -> int:
        """运行冒烟测试"""
        print("💨 运行冒烟测试...")
        return self.run_tests("unit", coverage=False, markers=["fast"])


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="足球预测系统测试运行器")

    parser.add_argument(
        "test_type",
        choices=[
            "unit",
            "integration",
            "regression",
            "e2e",
            "all",
            "quick",
            "full",
            "ci",
            "smoke",
        ],
        help="要运行的测试类型",
    )

    parser.add_argument("--no-coverage", action="store_true", help="不收集代码覆盖率")

    parser.add_argument("--quiet", action="store_true", help="静默模式,减少输出")

    parser.add_argument("--parallel", action="store_true", help="并行运行测试")

    parser.add_argument("--markers", nargs="*", help="pytest标记过滤器")

    args = parser.parse_args()

    runner = TestRunner()

    # 根据不同的测试类型调用不同的方法
    if args.test_type == "quick":
        result = runner.run_quick_tests()
    elif args.test_type == "full":
        result = runner.run_full_tests()
    elif args.test_type == "ci":
        result = runner.run_ci_tests()
    elif args.test_type == "smoke":
        result = runner.run_smoke_tests()
    else:
        result = runner.run_tests(
            test_type=args.test_type,
            coverage=not args.no_coverage,
            verbose=not args.quiet,
            parallel=args.parallel,
            markers=args.markers,
        )

    sys.exit(result)


if __name__ == "__main__":
    main()
