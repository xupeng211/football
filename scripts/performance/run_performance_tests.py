#!/usr/bin/env python3
"""
Performance Test Runner

This script orchestrates performance testing with different load scenarios
and generates comprehensive performance reports.
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TestScenario:
    """Performance test scenario configuration."""

    name: str
    description: str
    users: int
    spawn_rate: int
    duration: int  # seconds
    host: str
    user_classes: list[str]
    expected_rps: float
    max_error_rate: float
    max_avg_response_time: int  # milliseconds


class PerformanceTestRunner:
    """Manages execution of performance test scenarios."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.test_dir = self.project_root / "tests" / "performance"
        self.results_dir = self.project_root / "performance_results"
        self.results_dir.mkdir(exist_ok=True)

        # Test scenarios
        self.scenarios = {
            "smoke": TestScenario(
                name="smoke",
                description="Quick smoke test to verify API functionality",
                users=1,
                spawn_rate=1,
                duration=30,
                host="http://localhost:8000",
                user_classes=["LightLoadTest"],
                expected_rps=5.0,
                max_error_rate=5.0,
                max_avg_response_time=2000,
            ),
            "light": TestScenario(
                name="light",
                description="Light load simulation - normal usage patterns",
                users=5,
                spawn_rate=1,
                duration=120,
                host="http://localhost:8000",
                user_classes=["LightLoadTest"],
                expected_rps=20.0,
                max_error_rate=2.0,
                max_avg_response_time=1500,
            ),
            "medium": TestScenario(
                name="medium",
                description="Medium load simulation - busy periods",
                users=20,
                spawn_rate=2,
                duration=300,
                host="http://localhost:8000",
                user_classes=["MediumLoadTest"],
                expected_rps=80.0,
                max_error_rate=3.0,
                max_avg_response_time=2000,
            ),
            "heavy": TestScenario(
                name="heavy",
                description="Heavy load simulation - peak usage",
                users=50,
                spawn_rate=5,
                duration=600,
                host="http://localhost:8000",
                user_classes=["HeavyLoadTest"],
                expected_rps=150.0,
                max_error_rate=5.0,
                max_avg_response_time=3000,
            ),
            "stress": TestScenario(
                name="stress",
                description="Stress test - beyond normal capacity",
                users=100,
                spawn_rate=10,
                duration=300,
                host="http://localhost:8000",
                user_classes=["HeavyLoadTest"],
                expected_rps=200.0,
                max_error_rate=10.0,
                max_avg_response_time=5000,
            ),
            "spike": TestScenario(
                name="spike",
                description="Spike test - sudden load increase",
                users=200,
                spawn_rate=50,
                duration=180,
                host="http://localhost:8000",
                user_classes=["HeavyLoadTest"],
                expected_rps=300.0,
                max_error_rate=15.0,
                max_avg_response_time=8000,
            ),
        }

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        try:
            subprocess.run(["locust", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Locust not found. Install with: pip install locust")
            return False

    def check_api_health(self, host: str) -> bool:
        """Check if API is healthy before running tests."""
        try:
            import requests

            response = requests.get(f"{host}/health/live", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return False

    def run_scenario(
        self, scenario: TestScenario, output_file: Path = None
    ) -> dict[str, Any]:
        """Run a single performance test scenario."""

        print(f"🚀 Running scenario: {scenario.name}")
        print(f"   Description: {scenario.description}")
        print(f"   Users: {scenario.users}")
        print(f"   Duration: {scenario.duration}s")
        print(f"   Host: {scenario.host}")

        # Check API health
        if not self.check_api_health(scenario.host):
            return {
                "scenario": scenario.name,
                "status": "failed",
                "error": "API health check failed",
            }

        # Prepare output file
        if output_file is None:
            timestamp = int(time.time())
            output_file = self.results_dir / f"{scenario.name}_{timestamp}.json"

        # Build locust command
        locust_file = self.test_dir / "locustfile.py"

        cmd = [
            "locust",
            "-f",
            str(locust_file),
            "--host",
            scenario.host,
            "--users",
            str(scenario.users),
            "--spawn-rate",
            str(scenario.spawn_rate),
            "--run-time",
            f"{scenario.duration}s",
            "--headless",
            "--only-summary",
            "--html",
            str(output_file.with_suffix(".html")),
            "--csv",
            str(output_file.with_suffix("")),
            "--print-stats",
        ]

        # Add user classes if specified
        if scenario.user_classes:
            # Note: Locust doesn't directly support specifying user classes via CLI
            # This would require modifying the locustfile or using tags
            pass

        try:
            print(f"📊 Executing: {' '.join(cmd)}")

            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=scenario.duration + 60,  # Extra timeout buffer
            )
            end_time = time.time()

            # Parse results
            results = self._parse_results(scenario, result, start_time, end_time)

            # Save results to JSON
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)

            print(f"✅ Scenario completed: {scenario.name}")
            print(f"   Results saved to: {output_file}")

            return results

        except subprocess.TimeoutExpired:
            return {
                "scenario": scenario.name,
                "status": "timeout",
                "error": "Test execution timed out",
            }
        except Exception as e:
            return {"scenario": scenario.name, "status": "error", "error": str(e)}

    def _parse_results(
        self,
        scenario: TestScenario,
        result: subprocess.CompletedProcess,
        start_time: float,
        end_time: float,
    ) -> dict[str, Any]:
        """Parse Locust test results."""

        execution_time = end_time - start_time

        # Basic result structure
        results = {
            "scenario": scenario.name,
            "description": scenario.description,
            "status": "completed" if result.returncode == 0 else "failed",
            "execution_time": execution_time,
            "configuration": {
                "users": scenario.users,
                "spawn_rate": scenario.spawn_rate,
                "duration": scenario.duration,
                "host": scenario.host,
            },
            "output": {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            },
        }

        # Parse performance metrics from output
        try:
            lines = result.stdout.split("\n")

            # Look for summary statistics
            for line in lines:
                if "requests" in line and "failures" in line:
                    # Parse summary line
                    # Example: " 250    100      0(0.00%)     1.2    0.5     2.1    5.4     8.2    0.0"
                    parts = line.split()
                    if len(parts) >= 8:
                        results["metrics"] = {
                            "total_requests": int(parts[1])
                            if parts[1].isdigit()
                            else 0,
                            "failures": int(parts[2]) if parts[2].isdigit() else 0,
                            "median_response_time": float(parts[4])
                            if parts[4].replace(".", "").isdigit()
                            else 0,
                            "average_response_time": float(parts[5])
                            if parts[5].replace(".", "").isdigit()
                            else 0,
                            "min_response_time": float(parts[6])
                            if parts[6].replace(".", "").isdigit()
                            else 0,
                            "max_response_time": float(parts[7])
                            if parts[7].replace(".", "").isdigit()
                            else 0,
                        }
                        break

            # Calculate derived metrics
            if "metrics" in results:
                metrics = results["metrics"]
                total_requests = metrics["total_requests"]
                failures = metrics["failures"]

                if total_requests > 0:
                    metrics["error_rate"] = (failures / total_requests) * 100
                    metrics["requests_per_second"] = total_requests / execution_time
                    metrics["success_rate"] = (
                        (total_requests - failures) / total_requests
                    ) * 100

                # Evaluate against scenario expectations
                results["evaluation"] = self._evaluate_performance(scenario, metrics)

        except Exception as e:
            results["parse_error"] = str(e)

        return results

    def _evaluate_performance(
        self, scenario: TestScenario, metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate performance against scenario expectations."""

        evaluation = {"passed": True, "issues": []}

        # Check error rate
        error_rate = metrics.get("error_rate", 0)
        if error_rate > scenario.max_error_rate:
            evaluation["passed"] = False
            evaluation["issues"].append(
                f"Error rate {error_rate:.2f}% exceeds maximum {scenario.max_error_rate}%"
            )

        # Check average response time
        avg_response_time = metrics.get("average_response_time", 0)
        if avg_response_time > scenario.max_avg_response_time:
            evaluation["passed"] = False
            evaluation["issues"].append(
                f"Average response time {avg_response_time:.2f}ms exceeds maximum {scenario.max_avg_response_time}ms"
            )

        # Check requests per second
        rps = metrics.get("requests_per_second", 0)
        if rps < scenario.expected_rps:
            evaluation["issues"].append(
                f"RPS {rps:.2f} below expected {scenario.expected_rps}"
            )
            # Don't fail on RPS - it's more of a capacity indicator

        return evaluation

    def run_test_suite(
        self, scenarios: list[str] = None, host: str = None
    ) -> dict[str, Any]:
        """Run a suite of performance tests."""

        if scenarios is None:
            scenarios = ["smoke", "light", "medium"]  # Default suite

        print("🎯 Starting Performance Test Suite")
        print(f"Scenarios: {', '.join(scenarios)}")

        results = {"suite_start_time": time.time(), "scenarios": {}, "summary": {}}

        passed_scenarios = 0
        total_scenarios = len(scenarios)

        for scenario_name in scenarios:
            if scenario_name not in self.scenarios:
                print(f"⚠️  Unknown scenario: {scenario_name}")
                continue

            scenario = self.scenarios[scenario_name]

            # Override host if provided
            if host:
                scenario.host = host

            # Run scenario
            scenario_result = self.run_scenario(scenario)
            results["scenarios"][scenario_name] = scenario_result

            # Check if passed
            if scenario_result.get("status") == "completed" and scenario_result.get(
                "evaluation", {}
            ).get("passed", False):
                passed_scenarios += 1
                print(f"✅ {scenario_name}: PASSED")
            else:
                print(f"❌ {scenario_name}: FAILED")
                issues = scenario_result.get("evaluation", {}).get("issues", [])
                for issue in issues:
                    print(f"   - {issue}")

            # Brief pause between scenarios
            time.sleep(5)

        # Generate summary
        results["suite_end_time"] = time.time()
        results["summary"] = {
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "failed_scenarios": total_scenarios - passed_scenarios,
            "success_rate": (passed_scenarios / total_scenarios) * 100
            if total_scenarios > 0
            else 0,
            "overall_status": "PASSED"
            if passed_scenarios == total_scenarios
            else "FAILED",
        }

        print("\n📋 Performance Test Suite Summary:")
        print(f"Total scenarios: {total_scenarios}")
        print(f"Passed: {passed_scenarios}")
        print(f"Failed: {total_scenarios - passed_scenarios}")
        print(f"Success rate: {results['summary']['success_rate']:.1f}%")
        print(f"Overall status: {results['summary']['overall_status']}")

        return results

    def generate_report(self, results: dict[str, Any]) -> str:
        """Generate a comprehensive performance test report."""

        report_lines = [
            "# Performance Test Report",
            "",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            "",
            f"- **Total Scenarios:** {results['summary']['total_scenarios']}",
            f"- **Passed:** {results['summary']['passed_scenarios']}",
            f"- **Failed:** {results['summary']['failed_scenarios']}",
            f"- **Success Rate:** {results['summary']['success_rate']:.1f}%",
            f"- **Overall Status:** {results['summary']['overall_status']}",
            "",
            "## Scenario Results",
            "",
        ]

        for scenario_name, scenario_result in results["scenarios"].items():
            status_emoji = (
                "✅" if scenario_result.get("status") == "completed" else "❌"
            )

            report_lines.extend(
                [
                    f"### {status_emoji} {scenario_name.title()}",
                    "",
                    f"**Description:** {scenario_result.get('description', 'N/A')}",
                    f"**Status:** {scenario_result.get('status', 'Unknown')}",
                    "",
                ]
            )

            # Add metrics if available
            if "metrics" in scenario_result:
                metrics = scenario_result["metrics"]
                report_lines.extend(
                    [
                        "**Performance Metrics:**",
                        "",
                        f"- Total Requests: {metrics.get('total_requests', 'N/A')}",
                        f"- Error Rate: {metrics.get('error_rate', 0):.2f}%",
                        f"- Average Response Time: {metrics.get('average_response_time', 0):.2f}ms",
                        f"- Requests per Second: {metrics.get('requests_per_second', 0):.2f}",
                        "",
                    ]
                )

            # Add evaluation results
            if "evaluation" in scenario_result:
                evaluation = scenario_result["evaluation"]
                status = "PASSED" if evaluation.get("passed", False) else "FAILED"
                report_lines.append(f"**Evaluation:** {status}")

                if evaluation.get("issues"):
                    report_lines.extend(["", "**Issues:**", ""])
                    for issue in evaluation["issues"]:
                        report_lines.append(f"- {issue}")

                report_lines.append("")

        return "\n".join(report_lines)


def main():
    """Main CLI interface for performance testing."""

    parser = argparse.ArgumentParser(
        description="Football Prediction System Performance Test Runner"
    )

    parser.add_argument(
        "--scenario",
        choices=["smoke", "light", "medium", "heavy", "stress", "spike"],
        help="Run a specific scenario",
    )

    parser.add_argument(
        "--suite",
        nargs="+",
        default=["smoke", "light", "medium"],
        help="Run a suite of scenarios",
    )

    parser.add_argument(
        "--host", default="http://localhost:8000", help="Target host for testing"
    )

    parser.add_argument(
        "--report", action="store_true", help="Generate detailed report"
    )

    args = parser.parse_args()

    runner = PerformanceTestRunner()

    # Check dependencies
    if not runner.check_dependencies():
        sys.exit(1)

    try:
        if args.scenario:
            # Run single scenario
            scenario = runner.scenarios[args.scenario]
            scenario.host = args.host
            result = runner.run_scenario(scenario)

            if args.report:
                report = runner.generate_report({"scenarios": {args.scenario: result}})
                print("\n" + report)

        else:
            # Run test suite
            results = runner.run_test_suite(args.suite, args.host)

            if args.report:
                report = runner.generate_report(results)

                # Save report
                report_file = (
                    runner.results_dir / f"performance_report_{int(time.time())}.md"
                )
                with open(report_file, "w") as f:
                    f.write(report)

                print(f"\n📄 Report saved to: {report_file}")
                print("\n" + report)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
