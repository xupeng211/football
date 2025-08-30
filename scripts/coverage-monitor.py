#!/usr/bin/env python3
"""
Advanced test coverage monitoring and reporting script.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple

from defusedxml import ElementTree as ET


class CoverageMonitor:
    def __init__(self, target_coverage: float = 85.0):
        self.target_coverage = target_coverage
        self.project_root = Path(__file__).parent.parent

    def run_tests_with_coverage(self) -> Tuple[bool, Dict]:
        """Run tests and generate coverage report."""
        print("🧪 Running tests with coverage...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "--cov=.",
            "--cov-report=xml:coverage.xml",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "-v",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            success = result.returncode == 0
            coverage_data = self._parse_coverage_xml()

            return success, coverage_data

        except subprocess.TimeoutExpired:
            print("❌ Tests timed out after 5 minutes")
            return False, {}
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False, {}

    def _parse_coverage_xml(self) -> Dict:
        """Parse coverage XML report."""
        xml_path = self.project_root / "coverage.xml"
        if not xml_path.exists():
            return {}

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Get overall coverage from root element
            line_rate = float(root.get("line-rate", 0)) * 100
            branch_rate = float(root.get("branch-rate", 0)) * 100

            # Get per-package coverage
            packages = {}
            for package in root.findall(".//package"):
                name = package.get("name", "unknown")
                pkg_line_rate = float(package.get("line-rate", 0)) * 100
                packages[name] = pkg_line_rate

            return {
                "overall_coverage": line_rate,
                "branch_coverage": branch_rate,
                "packages": packages,
            }

        except Exception as e:
            print(f"⚠️  Error parsing coverage XML: {e}")
            return {}

    def generate_report(self, test_success: bool, coverage_data: Dict) -> Dict:
        """Generate comprehensive coverage report."""
        report = {
            "timestamp": subprocess.check_output(["date", "-Iseconds"])
            .decode()
            .strip(),
            "test_success": test_success,
            "target_coverage": self.target_coverage,
            "coverage_data": coverage_data,
        }

        if coverage_data:
            overall = coverage_data.get("overall_coverage", 0)
            report["coverage_status"] = (
                "PASS" if overall >= self.target_coverage else "FAIL"
            )
            report["coverage_gap"] = max(0, self.target_coverage - overall)
        else:
            report["coverage_status"] = "ERROR"
            report["coverage_gap"] = self.target_coverage

        return report

    def print_summary(self, report: Dict) -> None:
        """Print coverage summary to console."""
        print("\n" + "=" * 60)
        print("📊 COVERAGE REPORT SUMMARY")
        print("=" * 60)

        status_emoji = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}

        status = report.get("coverage_status", "ERROR")
        print(f"Status: {status_emoji.get(status, '❓')} {status}")

        if report.get("coverage_data"):
            coverage = report["coverage_data"].get("overall_coverage", 0)
            print(f"Overall Coverage: {coverage:.2f}%")
            print(f"Target Coverage: {report['target_coverage']:.2f}%")

            if report.get("coverage_gap", 0) > 0:
                print(f"Gap to Target: {report['coverage_gap']:.2f}%")

        print(f"Tests Passed: {'✅' if report['test_success'] else '❌'}")
        print("=" * 60)

    def save_report(self, report: Dict) -> None:
        """Save report to JSON file."""
        report_path = self.project_root / "coverage-report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"📄 Report saved to: {report_path}")

    def run_diff_coverage(self, base_branch: str = "main") -> None:
        """Run diff-cover to check coverage on changed lines."""
        print(f"🔍 Running diff-cover against {base_branch}...")

        try:
            cmd = [
                "diff-cover",
                "coverage.xml",
                f"--compare-branch={base_branch}",
            ]
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                print("✅ Diff coverage check passed")
            else:
                print("❌ Diff coverage check failed")
                print(result.stdout)

        except FileNotFoundError:
            print("⚠️  diff-cover not installed, skipping diff coverage check")
        except Exception as e:
            print(f"❌ Error running diff-cover: {e}")


def main() -> None:
    """Main entry point."""
    target_coverage = float(sys.argv[1]) if len(sys.argv) > 1 else 85.0

    monitor = CoverageMonitor(target_coverage)

    # Run tests and generate coverage
    test_success, coverage_data = monitor.run_tests_with_coverage()

    # Generate and display report
    report = monitor.generate_report(test_success, coverage_data)
    monitor.print_summary(report)
    monitor.save_report(report)

    # Run diff coverage if available
    monitor.run_diff_coverage()

    # Exit with appropriate code
    if report["coverage_status"] == "PASS" and test_success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
