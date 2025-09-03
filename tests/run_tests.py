#!/usr/bin/env python3
"""
测试运行脚本

提供不同场景下的测试运行命令。
"""

import subprocess
import sys


def run_command(cmd: list[str], description: str) -> int:
    """运行命令并显示结果"""
    print(f"\n🚀 {description}")
    print(f"命令: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, check=False, capture_output=False)

    if result.returncode == 0:
        print(f"✅ {description} 成功")
    else:
        print(f"❌ {description} 失败 (退出码: {result.returncode})")

    return result.returncode


def main():
    """主函数"""
    print("🧪 足球预测系统测试套件")
    print("=" * 60)

    test_scenarios = [
        {"cmd": ["pytest", "-m", "unit and fast", "-v"], "desc": "快速单元测试"},
        {"cmd": ["pytest", "-m", "unit and api", "-v"], "desc": "API单元测试"},
        {"cmd": ["pytest", "-m", "async", "-v"], "desc": "异步测试"},
        {
            "cmd": ["pytest", "-m", "integration", "-v", "--disable-warnings"],
            "desc": "集成测试",
        },
        {"cmd": ["pytest", "-m", "performance", "-v"], "desc": "性能测试"},
        {"cmd": ["pytest", "-m", "e2e", "-v"], "desc": "端到端测试"},
        {"cmd": ["pytest", "--co", "-q"], "desc": "收集所有测试(不运行)"},
        {
            "cmd": ["pytest", "--cov=src", "--cov-report=term-missing"],
            "desc": "覆盖率测试",
        },
    ]

    if len(sys.argv) > 1:
        scenario_name = sys.argv[1]
        scenarios_map = {
            "fast": test_scenarios[0],
            "api": test_scenarios[1],
            "async": test_scenarios[2],
            "integration": test_scenarios[3],
            "performance": test_scenarios[4],
            "e2e": test_scenarios[5],
            "collect": test_scenarios[6],
            "coverage": test_scenarios[7],
        }

        if scenario_name in scenarios_map:
            scenario = scenarios_map[scenario_name]
            return run_command(scenario["cmd"], scenario["desc"])
        print(f"❌ 未知的测试场景: {scenario_name}")
        print("可用场景:", ", ".join(scenarios_map.keys()))
        return 1

    # 运行所有场景
    failed_count = 0
    for scenario in test_scenarios:
        result = run_command(scenario["cmd"], scenario["desc"])
        if result != 0:
            failed_count += 1

    print("\n📊 总结:")
    print(f"总场景数: {len(test_scenarios)}")
    print(f"成功: {len(test_scenarios) - failed_count}")
    print(f"失败: {failed_count}")

    return failed_count


if __name__ == "__main__":
    sys.exit(main())
