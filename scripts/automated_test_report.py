#!/usr/bin/env python3
"""
自动化测试报告生成脚本

功能:
- 运行完整测试套件
- 生成测试覆盖率报告
- 生成HTML和JSON格式报告
- 发送测试结果通知
"""

import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict


class TestReportGenerator:
    """测试报告生成器"""

    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.reports_dir = self.project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "project": "football-predict-system",
            "test_results": {},
            "coverage": {},
            "summary": {},
        }

    def run_tests_with_coverage(self) -> Dict:
        """运行测试并生成覆盖率报告"""
        print("🧪 Running comprehensive test suite with coverage...")

        # 定义测试目录
        test_dirs = [
            "tests/unit/models/test_predictor_simple.py",
            "tests/unit/data_pipeline/test_feature_engineer_simple.py",
            "tests/unit/trainer/test_fit_xgb_simple.py",
            "tests/unit/data_pipeline/test_sources_simple.py",
            "tests/unit/models/test_registry_simple.py",
            "tests/unit/apps/backtest/test_engine_simple.py",
            "tests/unit/apps/api/test_routers_comprehensive.py",
            "tests/integration/test_api_routes_simple.py",
        ]

        # 构建pytest命令
        cmd = [
            "pytest",
            *test_dirs,
            "-v",
            "--cov=.",
            "--cov-report=html:htmlcov-report",
            "--cov-report=xml:coverage-report.xml",
            "--cov-report=json:coverage-report.json",
            "--cov-report=term-missing",
            "--junit-xml=test-results.xml",
            "--tb=short",
        ]

        try:
            # 运行测试
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )

            # 解析测试结果
            test_results = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }

            self.report_data["test_results"] = test_results

            print(f"✅ Tests completed with exit code: {result.returncode}")
            return test_results

        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return {"success": False, "error": str(e)}

    def parse_coverage_report(self) -> Dict:
        """解析覆盖率报告"""
        print("📊 Parsing coverage report...")

        coverage_file = self.project_root / "coverage-report.json"

        if not coverage_file.exists():
            print("⚠️ Coverage report not found")
            return {}

        try:
            with open(coverage_file) as f:
                coverage_data = json.load(f)

            # 提取关键指标
            totals = coverage_data.get("totals", {})
            coverage_summary = {
                "overall_coverage": round(totals.get("percent_covered", 0), 2),
                "lines_covered": totals.get("covered_lines", 0),
                "lines_total": totals.get("num_statements", 0),
                "missing_lines": totals.get("missing_lines", 0),
                "excluded_lines": totals.get("excluded_lines", 0),
            }

            # 按模块分析覆盖率
            files_coverage = {}
            for file_path, file_data in coverage_data.get("files", {}).items():
                summary = file_data.get("summary", {})
                files_coverage[file_path] = {
                    "coverage": round(summary.get("percent_covered", 0), 2),
                    "lines_covered": summary.get("covered_lines", 0),
                    "lines_total": summary.get("num_statements", 0),
                }

            self.report_data["coverage"] = {
                "summary": coverage_summary,
                "by_file": files_coverage,
            }

            print(f"📈 Overall coverage: {coverage_summary['overall_coverage']}%")
            return coverage_summary

        except Exception as e:
            print(f"❌ Error parsing coverage: {e}")
            return {}

    def parse_test_results(self) -> Dict:
        """解析JUnit XML测试结果"""
        print("🔍 Parsing test results...")

        junit_file = self.project_root / "test-results.xml"

        if not junit_file.exists():
            print("⚠️ JUnit results not found")
            return {}

        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()

            # 提取测试统计
            test_stats = {
                "total_tests": int(root.get("tests", 0)),
                "passed_tests": 0,
                "failed_tests": int(root.get("failures", 0)),
                "error_tests": int(root.get("errors", 0)),
                "skipped_tests": int(root.get("skipped", 0)),
                "execution_time": float(root.get("time", 0)),
            }

            test_stats["passed_tests"] = (
                test_stats["total_tests"]
                - test_stats["failed_tests"]
                - test_stats["error_tests"]
                - test_stats["skipped_tests"]
            )

            # 计算成功率
            if test_stats["total_tests"] > 0:
                test_stats["success_rate"] = round(
                    test_stats["passed_tests"] / test_stats["total_tests"] * 100, 2
                )
            else:
                test_stats["success_rate"] = 0

            # 提取失败测试详情
            failed_tests = []
            for testcase in root.iter("testcase"):
                failure = testcase.find("failure")
                error = testcase.find("error")

                if failure is not None or error is not None:
                    failed_tests.append(
                        {
                            "name": testcase.get("name", "unknown"),
                            "classname": testcase.get("classname", "unknown"),
                            "time": float(testcase.get("time", 0)),
                            "error_type": failure.get("type")
                            if failure is not None
                            else error.get("type"),
                            "message": (
                                failure.text if failure is not None else error.text
                            )[:200]
                            + "...",
                        }
                    )

            test_stats["failed_test_details"] = failed_tests

            self.report_data["test_results"]["statistics"] = test_stats

            print(f"🎯 Test success rate: {test_stats['success_rate']}%")
            return test_stats

        except Exception as e:
            print(f"❌ Error parsing test results: {e}")
            return {}

    def generate_summary(self) -> Dict:
        """生成测试总结"""
        print("📝 Generating test summary...")

        test_stats = self.report_data.get("test_results", {}).get("statistics", {})
        coverage_summary = self.report_data.get("coverage", {}).get("summary", {})

        # 计算质量评分
        quality_score = 0
        if test_stats.get("success_rate", 0) >= 90:
            quality_score += 40
        elif test_stats.get("success_rate", 0) >= 80:
            quality_score += 30
        elif test_stats.get("success_rate", 0) >= 70:
            quality_score += 20

        if coverage_summary.get("overall_coverage", 0) >= 85:
            quality_score += 40
        elif coverage_summary.get("overall_coverage", 0) >= 75:
            quality_score += 30
        elif coverage_summary.get("overall_coverage", 0) >= 65:
            quality_score += 20

        if test_stats.get("total_tests", 0) >= 50:
            quality_score += 20
        elif test_stats.get("total_tests", 0) >= 30:
            quality_score += 15
        elif test_stats.get("total_tests", 0) >= 20:
            quality_score += 10

        # 生成建议
        recommendations = []

        if test_stats.get("success_rate", 0) < 90:
            recommendations.append("修复失败的测试用例")

        if coverage_summary.get("overall_coverage", 0) < 85:
            recommendations.append("提升测试覆盖率到85%以上")

        if test_stats.get("total_tests", 0) < 50:
            recommendations.append("增加更多测试用例")

        if len(test_stats.get("failed_test_details", [])) > 5:
            recommendations.append("重点关注失败率较高的测试模块")

        summary = {
            "quality_score": quality_score,
            "grade": self._get_quality_grade(quality_score),
            "total_tests": test_stats.get("total_tests", 0),
            "success_rate": test_stats.get("success_rate", 0),
            "coverage_rate": coverage_summary.get("overall_coverage", 0),
            "execution_time": test_stats.get("execution_time", 0),
            "recommendations": recommendations,
        }

        self.report_data["summary"] = summary

        print(f"🏆 Quality score: {quality_score}/100 ({summary['grade']})")
        return summary

    def _get_quality_grade(self, score: int) -> str:
        """根据评分获取质量等级"""
        if score >= 90:
            return "A+ (优秀)"
        elif score >= 80:
            return "A (良好)"
        elif score >= 70:
            return "B (中等)"
        elif score >= 60:
            return "C (及格)"
        else:
            return "D (需改进)"

    def save_reports(self):
        """保存所有报告"""
        print("💾 Saving reports...")

        # 保存JSON报告
        json_file = self.reports_dir / f"test_report_{self.timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)

        # 生成HTML报告
        html_report = self._generate_html_report()
        html_file = self.reports_dir / f"test_report_{self.timestamp}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_report)

        # 生成Markdown摘要
        md_summary = self._generate_markdown_summary()
        md_file = self.reports_dir / f"test_summary_{self.timestamp}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_summary)

        print(f"📄 Reports saved to {self.reports_dir}")
        return {"json": json_file, "html": html_file, "markdown": md_file}

    def _generate_html_report(self) -> str:
        """生成HTML报告"""
        summary = self.report_data.get("summary", {})
        test_stats = self.report_data.get("test_results", {}).get("statistics", {})
        coverage = self.report_data.get("coverage", {}).get("summary", {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Football Prediction System - Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 5px; }}
        .success {{ color: #4CAF50; }}
        .warning {{ color: #FF9800; }}
        .error {{ color: #F44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 Football Prediction System - Test Report</h1>
        <p>Generated: {self.report_data["timestamp"]}</p>
    </div>

    <div class="summary">
        <h2>📊 Summary</h2>
        <div class="metric">
            <strong>Quality Score:</strong> {summary.get("quality_score", 0)}/100
            <br><strong>Grade:</strong> {summary.get("grade", "N/A")}
        </div>
        <div class="metric">
            <strong>Total Tests:</strong> {test_stats.get("total_tests", 0)}
            <br><strong>Success Rate:</strong> {test_stats.get("success_rate", 0)}%
        </div>
        <div class="metric">
            <strong>Coverage:</strong> {coverage.get("overall_coverage", 0)}%
            <br><strong>Execution Time:</strong> {test_stats.get("execution_time", 0):.2f}s
        </div>
    </div>

    <h2>🎯 Test Results</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Passed Tests</td><td class="success">{test_stats.get("passed_tests", 0)}</td></tr>
        <tr><td>Failed Tests</td><td class="error">{test_stats.get("failed_tests", 0)}</td></tr>
        <tr><td>Skipped Tests</td><td class="warning">{test_stats.get("skipped_tests", 0)}</td></tr>
    </table>

    <h2>📈 Coverage Details</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Lines Covered</td><td>{coverage.get("lines_covered", 0)}</td></tr>
        <tr><td>Total Lines</td><td>{coverage.get("lines_total", 0)}</td></tr>
        <tr><td>Missing Lines</td><td>{coverage.get("missing_lines", 0)}</td></tr>
    </table>

    <h2>💡 Recommendations</h2>
    <ul>
        {"".join(f"<li>{rec}</li>" for rec in summary.get("recommendations", []))}
    </ul>
</body>
</html>
"""
        return html

    def _generate_markdown_summary(self) -> str:
        """生成Markdown摘要"""
        summary = self.report_data.get("summary", {})
        test_stats = self.report_data.get("test_results", {}).get("statistics", {})
        coverage = self.report_data.get("coverage", {}).get("summary", {})

        md = f"""# 🏆 Test Report Summary

**Generated:** {self.report_data["timestamp"]}
**Project:** {self.report_data["project"]}

## 📊 Overview

| Metric | Value |
|--------|-------|
| Quality Score | {summary.get("quality_score", 0)}/100 ({summary.get("grade", "N/A")}) |
| Total Tests | {test_stats.get("total_tests", 0)} |
| Success Rate | {test_stats.get("success_rate", 0)}% |
| Coverage Rate | {coverage.get("overall_coverage", 0)}% |
| Execution Time | {test_stats.get("execution_time", 0):.2f}s |

## ✅ Test Results

- **Passed:** {test_stats.get("passed_tests", 0)}
- **Failed:** {test_stats.get("failed_tests", 0)}
- **Skipped:** {test_stats.get("skipped_tests", 0)}

## 📈 Coverage Metrics

- **Lines Covered:** {coverage.get("lines_covered", 0)}/{coverage.get("lines_total", 0)}
- **Coverage Rate:** {coverage.get("overall_coverage", 0)}%

## 💡 Recommendations

{chr(10).join(f"- {rec}" for rec in summary.get("recommendations", []))}

---
*Report generated by Football Prediction System Test Suite*
"""
        return md

    def run_full_analysis(self) -> Dict:
        """运行完整的测试分析"""
        print("🚀 Starting comprehensive test analysis...")
        start_time = time.time()

        try:
            # 1. 运行测试
            self.run_tests_with_coverage()

            # 2. 解析结果
            self.parse_coverage_report()
            self.parse_test_results()

            # 3. 生成总结
            self.generate_summary()

            # 4. 保存报告
            file_paths = self.save_reports()

            end_time = time.time()
            duration = end_time - start_time

            print(f"✅ Analysis completed in {duration:.2f} seconds")
            print(
                f"📊 Quality Score: {self.report_data['summary']['quality_score']}/100"
            )
            print(f"📄 Reports available at: {self.reports_dir}")

            return {
                "success": True,
                "duration": duration,
                "files": file_paths,
                "summary": self.report_data["summary"],
            }

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {"success": False, "error": str(e)}


def main():
    """主函数"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = None

    generator = TestReportGenerator(project_root)
    result = generator.run_full_analysis()

    # 返回适当的退出码
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
