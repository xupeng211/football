#!/usr/bin/env python3
"""
CI质量监控仪表板
获取并展示项目的CI质量指标
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class CIDashboard:
    def __init__(self):
        self.metrics = {}

    def get_ci_metrics(self):
        """获取CI质量指标"""
        print("📊 收集CI质量指标...")

        self.metrics = {
            "timestamp": datetime.now().isoformat(),
            "coverage": self.get_coverage(),
            "test_count": self.get_test_count(),
            "test_passed": self.get_test_results(),
            "security_issues": self.get_security_issues(),
            "code_quality": self.get_code_quality(),
            "dependencies": self.get_dependencies_status(),
        }
        return self.metrics

    def get_coverage(self):
        """获取测试覆盖率"""
        try:
            subprocess.run(  # nosec B603 B607 - 内部工具, 已知命令
                [
                    "python",
                    "-m",
                    "pytest",
                    "--cov=apps",
                    "--cov=data_pipeline",
                    "--cov=models",
                    "--cov-report=json",
                    "-q",
                    "--tb=no",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if Path("coverage.json").exists():
                with open("coverage.json") as f:
                    data = json.load(f)
                    return round(data["totals"]["percent_covered"], 2)
        except Exception as e:
            print(f"⚠️ 覆盖率检查失败: {e}")
        return 0.0

    def get_test_count(self):
        """获取测试数量"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            for line in result.stdout.split("\n"):
                if "collected" in line and "item" in line:
                    return int(line.split()[0])
        except Exception as e:
            print(f"⚠️ 测试计数失败: {e}")
        return 0

    def get_test_results(self):
        """获取测试通过情况"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--tb=no", "-q"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            output = result.stdout
            if "passed" in output:
                # 解析 "225 passed, 22 skipped" 格式
                for line in output.split("\n"):
                    if "passed" in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "passed,":
                                return int(parts[i - 1])
                            elif part == "passed":
                                return int(parts[i - 1])
        except Exception as e:
            print(f"⚠️ 测试结果检查失败: {e}")
        return 0

    def get_security_issues(self):
        """获取安全问题数量"""
        try:
            result = subprocess.run(
                ["bandit", "-r", ".", "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                data = json.loads(result.stdout)
                return len(data.get("results", []))
        except Exception as e:
            print(f"⚠️ 安全扫描失败: {e}")
        return -1  # -1 表示无法检查

    def get_code_quality(self):
        """获取代码质量分数"""
        try:
            result = subprocess.run(
                ["ruff", "check", ".", "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                issues = json.loads(result.stdout)
                return max(0, 100 - len(issues))
            else:
                return 100  # 没有问题
        except Exception as e:
            print(f"⚠️ 代码质量检查失败: {e}")
        return -1

    def get_dependencies_status(self):
        """检查依赖文件状态"""
        files = ["requirements.txt", "uv.lock", "pyproject.toml"]
        status = {}

        for file in files:
            path = Path(file)
            status[file] = {
                "exists": path.exists(),
                "size": path.stat().st_size if path.exists() else 0,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                if path.exists()
                else None,
            }

        return status

    def generate_report(self):
        """生成质量报告"""
        m = self.metrics

        print("\n" + "=" * 60)
        print(f"📊 CI质量报告 - {m['timestamp'][:19]}")
        print("=" * 60)

        # 测试覆盖率
        coverage = m["coverage"]
        if coverage >= 75:
            cov_icon = "🟢"
        elif coverage >= 50:
            cov_icon = "🟡"
        else:
            cov_icon = "🔴"
        print(f"{cov_icon} 测试覆盖率: {coverage}%")

        # 测试通过情况
        test_count = m["test_count"]
        test_passed = m["test_passed"]
        if test_passed == test_count and test_count > 0:
            test_icon = "🟢"
        elif test_passed > 0:
            test_icon = "🟡"
        else:
            test_icon = "🔴"
        print(f"{test_icon} 测试结果: {test_passed}/{test_count} 通过")

        # 安全问题
        security = m["security_issues"]
        if security == 0:
            sec_icon = "🟢"
        elif security == -1:
            sec_icon = "⚪"
            security = "无法检查"
        else:
            sec_icon = "🔴"
        print(f"{sec_icon} 安全问题: {security}")

        # 代码质量
        quality = m["code_quality"]
        if quality >= 90:
            qual_icon = "🟢"
        elif quality >= 70:
            qual_icon = "🟡"
        elif quality == -1:
            qual_icon = "⚪"
            quality = "无法检查"
        else:
            qual_icon = "🔴"
        print(f"{qual_icon} 代码质量: {quality}/100")

        # 依赖状态
        deps = m["dependencies"]
        missing_deps = [f for f, info in deps.items() if not info["exists"]]
        if not missing_deps:
            deps_icon = "🟢"
            deps_status = "完整"
        else:
            deps_icon = "🔴"
            deps_status = f"缺失: {', '.join(missing_deps)}"
        print(f"{deps_icon} 依赖文件: {deps_status}")

        print("=" * 60)

        # 总体评估
        score = self.calculate_overall_score()
        if score >= 90:
            print(f"🎉 总体评分: {score}/100 - 优秀!")
        elif score >= 70:
            print(f"👍 总体评分: {score}/100 - 良好")
        elif score >= 50:
            print(f"⚠️ 总体评分: {score}/100 - 需要改进")
        else:
            print(f"❌ 总体评分: {score}/100 - 急需修复")

        return score

    def calculate_overall_score(self):
        """计算总体质量分数"""
        m = self.metrics
        score = 0

        # 测试覆盖率 (30%)
        score += min(30, m["coverage"] * 30 / 100)

        # 测试通过率 (25%)
        if m["test_count"] > 0:
            test_rate = m["test_passed"] / m["test_count"]
            score += test_rate * 25

        # 代码质量 (25%)
        if m["code_quality"] >= 0:
            score += m["code_quality"] * 25 / 100

        # 安全状况 (10%)
        if m["security_issues"] == 0:
            score += 10
        elif m["security_issues"] > 0:
            score += max(0, 10 - m["security_issues"])

        # 依赖完整性 (10%)
        deps = m["dependencies"]
        essential_files = ["requirements.txt", "pyproject.toml"]
        if all(deps[f]["exists"] for f in essential_files):
            score += 10

        return round(score)

    def save_metrics(self, filename="ci-metrics.json"):
        """保存指标到文件"""
        with open(filename, "w") as f:
            json.dump(self.metrics, f, indent=2)
        print(f"📝 指标已保存到 {filename}")


def main():
    dashboard = CIDashboard()

    try:
        dashboard.get_ci_metrics()
        score = dashboard.generate_report()

        # 保存指标
        dashboard.save_metrics()

        # 根据分数决定退出码
        if score >= 70:
            sys.exit(0)  # 成功
        else:
            sys.exit(1)  # 需要改进

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
