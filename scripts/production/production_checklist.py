#!/usr/bin/env python3
"""
🏭 Football Predict System - Production Readiness Checklist

This script validates that all production requirements are met
before deploying the system to production environment.
"""

import json
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class CheckStatus(Enum):
    """Status of a production check."""

    PASS = "✅"
    FAIL = "❌"
    WARN = "⚠️"
    INFO = "ℹ️"


@dataclass
class CheckResult:
    """Result of a production readiness check."""

    name: str
    status: CheckStatus
    message: str
    details: str = ""


class ProductionChecker:
    """Production readiness checker for Football Predict System."""

    def __init__(self):
        self.results: list[CheckResult] = []
        self.root_dir = Path(__file__).parent.parent.parent

    def add_result(
        self, name: str, status: CheckStatus, message: str, details: str = ""
    ):
        """Add a check result."""
        self.results.append(CheckResult(name, status, message, details))

    def check_environment_config(self) -> None:
        """Check environment configuration files."""
        config_file = self.root_dir / "config" / "production.env.template"

        if config_file.exists():
            self.add_result(
                "Environment Template",
                CheckStatus.PASS,
                "Production environment template exists",
            )
        else:
            self.add_result(
                "Environment Template",
                CheckStatus.FAIL,
                "Production environment template missing",
                "Create config/production.env.template",
            )

    def check_database_config(self) -> None:
        """Check database configuration."""
        schema_file = self.root_dir / "sql" / "schema.sql"

        if schema_file.exists():
            self.add_result(
                "Database Schema", CheckStatus.PASS, "Database schema file exists"
            )
        else:
            self.add_result(
                "Database Schema",
                CheckStatus.FAIL,
                "Database schema file missing",
                "Create sql/schema.sql",
            )

    def check_monitoring_config(self) -> None:
        """Check monitoring configuration."""
        prometheus_config = (
            self.root_dir / "monitoring" / "prometheus" / "football_data_platform.yml"
        )
        grafana_dashboard = (
            self.root_dir
            / "monitoring"
            / "grafana"
            / "dashboards"
            / "data_platform_dashboard.json"
        )

        if prometheus_config.exists():
            self.add_result(
                "Prometheus Config", CheckStatus.PASS, "Prometheus configuration exists"
            )
        else:
            self.add_result(
                "Prometheus Config",
                CheckStatus.FAIL,
                "Prometheus configuration missing",
            )

        if grafana_dashboard.exists():
            self.add_result(
                "Grafana Dashboard",
                CheckStatus.PASS,
                "Grafana dashboard configuration exists",
            )
        else:
            self.add_result(
                "Grafana Dashboard",
                CheckStatus.FAIL,
                "Grafana dashboard configuration missing",
            )

    def check_deployment_scripts(self) -> None:
        """Check deployment scripts."""
        setup_script = (
            self.root_dir / "scripts" / "production" / "quick_production_setup.sh"
        )

        if setup_script.exists():
            if os.access(setup_script, os.X_OK):
                self.add_result(
                    "Production Setup Script",
                    CheckStatus.PASS,
                    "Production setup script exists and is executable",
                )
            else:
                self.add_result(
                    "Production Setup Script",
                    CheckStatus.WARN,
                    "Production setup script exists but is not executable",
                    "Run: chmod +x scripts/production/quick_production_setup.sh",
                )
        else:
            self.add_result(
                "Production Setup Script",
                CheckStatus.FAIL,
                "Production setup script missing",
            )

    def check_docker_config(self) -> None:
        """Check Docker configuration."""
        dockerfile = self.root_dir / "Dockerfile"
        docker_compose = self.root_dir / "docker-compose.yml"

        if dockerfile.exists():
            self.add_result("Dockerfile", CheckStatus.PASS, "Dockerfile exists")
        else:
            self.add_result(
                "Dockerfile",
                CheckStatus.WARN,
                "Dockerfile missing - consider containerized deployment",
            )

        if docker_compose.exists():
            self.add_result(
                "Docker Compose",
                CheckStatus.PASS,
                "Docker Compose configuration exists",
            )
        else:
            self.add_result(
                "Docker Compose",
                CheckStatus.WARN,
                "Docker Compose configuration missing",
            )

    def check_security_config(self) -> None:
        """Check security configuration."""
        # Check for secrets in configuration
        env_template = self.root_dir / "config" / "production.env.template"

        if env_template.exists():
            content = env_template.read_text()
            if "${" in content:
                self.add_result(
                    "Environment Security",
                    CheckStatus.PASS,
                    "Environment template uses variable substitution",
                )
            else:
                self.add_result(
                    "Environment Security",
                    CheckStatus.WARN,
                    "Environment template may contain hardcoded values",
                )

    def check_documentation(self) -> None:
        """Check documentation."""
        readme = self.root_dir / "README.md"

        if readme.exists():
            self.add_result("Documentation", CheckStatus.PASS, "README.md exists")
        else:
            self.add_result("Documentation", CheckStatus.FAIL, "README.md missing")

    def run_all_checks(self) -> None:
        """Run all production readiness checks."""
        print("🏭 Running Production Readiness Checks...")
        print("=" * 50)

        self.check_environment_config()
        self.check_database_config()
        self.check_monitoring_config()
        self.check_deployment_scripts()
        self.check_docker_config()
        self.check_security_config()
        self.check_documentation()

    def print_results(self) -> None:
        """Print check results."""
        print("\n📋 Production Readiness Results:")
        print("=" * 50)

        for result in self.results:
            print(f"{result.status.value} {result.name}: {result.message}")
            if result.details:
                print(f"   💡 {result.details}")

        # Summary
        pass_count = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        fail_count = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warn_count = sum(1 for r in self.results if r.status == CheckStatus.WARN)

        print("\n📊 Summary:")
        print(f"   ✅ Passed: {pass_count}")
        print(f"   ❌ Failed: {fail_count}")
        print(f"   ⚠️  Warnings: {warn_count}")

        if fail_count > 0:
            print("\n❌ Production readiness check FAILED")
            print(
                f"   Please fix {fail_count} critical issue(s) before deploying to production."
            )
            return False
        elif warn_count > 0:
            print("\n⚠️  Production readiness check PASSED with warnings")
            print(
                f"   Consider addressing {warn_count} warning(s) for optimal production setup."
            )
            return True
        else:
            print("\n🎉 Production readiness check PASSED")
            print("   System is ready for production deployment!")
            return True

    def save_report(self, filename: str = "production_readiness_report.json") -> None:
        """Save results to JSON file."""
        report_data = {
            "timestamp": "2025-09-03T10:34:00Z",
            "system": "football-predict-system",
            "version": "3.0.0",
            "checks": [
                {
                    "name": r.name,
                    "status": r.status.name,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.results
            ],
        }

        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Report saved to: {filename}")


def main():
    """Main function."""
    checker = ProductionChecker()
    checker.run_all_checks()
    success = checker.print_results()
    checker.save_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
