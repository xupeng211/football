#!/usr/bin/env python3
"""
Production Readiness Checklist for Football Data Platform.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    import redis
    import requests
    from sqlalchemy import text

    from football_predict_system.core.config import get_settings
    from football_predict_system.core.database import get_database_manager
    from football_predict_system.core.logging import get_logger, setup_logging
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装所有依赖: uv sync")
    sys.exit(1)

setup_logging()
logger = get_logger(__name__)


class ProductionChecker:
    """Production readiness checker."""

    def __init__(self):
        self.settings = get_settings()
        self.checks = []
        self.score = 0
        self.max_score = 0

    def add_check(self, name: str, status: bool, weight: int = 1, message: str = ""):
        """Add a check result."""
        self.checks.append(
            {
                "name": name,
                "status": status,
                "weight": weight,
                "message": message,
                "icon": "✅" if status else "❌",
            }
        )
        self.max_score += weight
        if status:
            self.score += weight

    async def check_environment_config(self):
        """Check environment configuration."""
        print("🔧 检查环境配置...")

        # Check API keys
        api_key = getattr(self.settings, "football_data_api_key", None)
        self.add_check(
            "Football API密钥",
            bool(api_key and api_key != "dev_football_data_api_key"),
            weight=3,
            message="生产环境必须配置真实API密钥",
        )

        # Check database config
        db_url = self.settings.database.url
        is_prod_db = not any(
            x in db_url.lower() for x in ["localhost", "127.0.0.1", "sqlite"]
        )
        self.add_check(
            "生产数据库配置",
            is_prod_db,
            weight=3,
            message="应使用远程PostgreSQL,避免本地数据库",
        )

        # Check Redis config
        redis_url = getattr(self.settings, "redis_url", "")
        is_prod_redis = not any(
            x in redis_url.lower() for x in ["localhost", "127.0.0.1"]
        )
        self.add_check(
            "生产Redis配置", is_prod_redis, weight=2, message="应使用远程Redis集群"
        )

        # Check environment
        env = getattr(self.settings, "environment", "development")
        self.add_check(
            "环境标识", env == "production", weight=1, message="ENV应设置为production"
        )

    async def check_api_connectivity(self):
        """Check API connectivity."""
        print("📡 检查API连接...")

        api_key = getattr(self.settings, "football_data_api_key", None)
        if not api_key:
            self.add_check("API连接测试", False, weight=2, message="API密钥未配置")
            return

        try:
            response = requests.get(
                "https://api.football-data.org/v4/competitions",
                headers={"X-Auth-Token": api_key},
                timeout=10,
            )
            success = response.status_code == 200

            if success:
                data = response.json()
                comp_count = len(data.get("competitions", []))
                message = f"成功获取 {comp_count} 个联赛信息"
            else:
                message = f"API返回错误: {response.status_code}"

            self.add_check("API连接测试", success, weight=2, message=message)

        except Exception as e:
            self.add_check("API连接测试", False, weight=2, message=f"连接失败: {e}")

    async def check_database_connectivity(self):
        """Check database connectivity."""
        print("🗄️ 检查数据库连接...")

        try:
            db_manager = get_database_manager()
            async with db_manager.get_async_session() as session:
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()

            self.add_check(
                "数据库连接",
                True,
                weight=3,
                message=f"PostgreSQL连接正常: {version[:50]}...",
            )

            # Check if tables exist
            async with db_manager.get_async_session() as session:
                result = await session.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'matches'"
                    )
                )
                table_exists = result.scalar() > 0

            self.add_check(
                "数据表结构",
                table_exists,
                weight=2,
                message="核心数据表存在"
                if table_exists
                else "需要执行 make data-setup",
            )

        except Exception as e:
            self.add_check("数据库连接", False, weight=3, message=f"连接失败: {e}")

    async def check_redis_connectivity(self):
        """Check Redis connectivity."""
        print("🚀 检查Redis连接...")

        try:
            redis_url = getattr(self.settings, "redis_url", "redis://localhost:6379/0")
            r = redis.from_url(redis_url)
            r.ping()

            # Test basic operations
            r.set("health_check", "ok", ex=60)
            value = r.get("health_check")

            self.add_check(
                "Redis连接", value == b"ok", weight=2, message="Redis读写测试通过"
            )

        except Exception as e:
            self.add_check("Redis连接", False, weight=2, message=f"连接失败: {e}")

    async def check_monitoring_setup(self):
        """Check monitoring setup."""
        print("📈 检查监控配置...")

        # Check Prometheus config
        prom_config = Path("monitoring/prometheus/football_data_platform.yml")
        self.add_check(
            "Prometheus告警规则",
            prom_config.exists(),
            weight=1,
            message="监控规则配置存在",
        )

        # Check Grafana dashboard
        grafana_dashboard = Path(
            "monitoring/grafana/dashboards/data_platform_dashboard.json"
        )
        self.add_check(
            "Grafana监控面板",
            grafana_dashboard.exists(),
            weight=1,
            message="监控面板配置存在",
        )

        # Check if Prometheus is accessible
        try:
            prom_url = "http://localhost:9090/api/v1/query?query=up"
            response = requests.get(prom_url, timeout=5)
            prom_accessible = response.status_code == 200
        except Exception as e:
            print(f"Prometheus连接检查失败: {e}")
            prom_accessible = False

        self.add_check(
            "Prometheus服务",
            prom_accessible,
            weight=2,
            message="Prometheus可访问"
            if prom_accessible
            else "需要启动: docker-compose up prometheus",
        )

    async def check_security_config(self):
        """Check security configuration."""
        print("🛡️ 检查安全配置...")

        # Check if debug mode is disabled
        debug_mode = getattr(self.settings, "debug", True)
        self.add_check(
            "调试模式关闭", not debug_mode, weight=2, message="生产环境应关闭DEBUG模式"
        )

        # Check JWT secret
        jwt_secret = getattr(self.settings, "jwt_secret_key", "")
        is_secure_secret = len(jwt_secret) >= 32 and jwt_secret != "dev-secret-key"
        self.add_check(
            "JWT密钥安全",
            is_secure_secret,
            weight=2,
            message="JWT密钥长度应≥32字符且非默认值",
        )

        # Check CORS settings
        cors_origins = getattr(self.settings, "cors_origins", ["*"])
        is_restricted_cors = "*" not in cors_origins
        self.add_check(
            "CORS安全配置",
            is_restricted_cors,
            weight=1,
            message="生产环境应限制CORS来源",
        )

    async def generate_report(self):
        """Generate comprehensive report."""

        # Calculate score
        percentage = (self.score / self.max_score * 100) if self.max_score > 0 else 0

        # Determine readiness level
        if percentage >= 90:
            level = "🟢 生产就绪"
            recommendation = "可以立即部署到生产环境"
        elif percentage >= 75:
            level = "🟡 基本就绪"
            recommendation = "修复关键问题后可部署"
        elif percentage >= 60:
            level = "🟠 需要改进"
            recommendation = "建议先在测试环境验证"
        else:
            level = "🔴 未就绪"
            recommendation = "需要完成基础配置才能使用"

        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": percentage,
            "readiness_level": level,
            "recommendation": recommendation,
            "checks": self.checks,
            "summary": {
                "total_checks": len(self.checks),
                "passed_checks": sum(1 for c in self.checks if c["status"]),
                "critical_issues": [
                    c for c in self.checks if not c["status"] and c["weight"] >= 3
                ],
                "warnings": [
                    c for c in self.checks if not c["status"] and c["weight"] < 3
                ],
            },
        }

        return report

    def print_report(self, report: dict):
        """Print formatted report."""
        print("\n" + "=" * 70)
        print("🏭 FOOTBALL DATA PLATFORM - 生产就绪度报告")
        print("=" * 70)
        print(f"📅 检查时间: {report['timestamp']}")
        print(f"📊 综合评分: {report['overall_score']:.1f}/100")
        print(f"🎯 就绪级别: {report['readiness_level']}")
        print(f"💡 建议: {report['recommendation']}")
        print()

        # Print checks by category
        categories = {
            "🔧 环境配置": [
                c
                for c in report["checks"]
                if any(x in c["name"] for x in ["密钥", "配置", "环境"])
            ],
            "📡 服务连接": [
                c
                for c in report["checks"]
                if any(x in c["name"] for x in ["连接", "API", "数据库", "Redis"])
            ],
            "📈 监控告警": [
                c
                for c in report["checks"]
                if any(x in c["name"] for x in ["监控", "Prometheus", "Grafana"])
            ],
            "🛡️ 安全设置": [
                c
                for c in report["checks"]
                if any(x in c["name"] for x in ["安全", "调试", "JWT", "CORS"])
            ],
        }

        for category, checks in categories.items():
            if checks:
                print(f"{category}")
                for check in checks:
                    print(f"  {check['icon']} {check['name']}: {check['message']}")
                print()

        # Critical issues
        if report["summary"]["critical_issues"]:
            print("🚨 关键问题 (必须解决):")
            for issue in report["summary"]["critical_issues"]:
                print(f"  ❌ {issue['name']}: {issue['message']}")
            print()

        # Next steps
        print("📋 下一步行动:")
        if report["overall_score"] >= 75:
            print("  1. 🚀 运行完整测试: make data-collect")
            print("  2. 📊 验证数据质量: make data-monitor")
            print("  3. 🔄 部署调度任务: make data-deploy-flows")
        else:
            print("  1. 🔧 修复上述关键配置问题")
            print(
                "  2. 🧪 重新运行检查: python scripts/production/production_checklist.py"
            )
            print("  3. 📋 完成基础配置后再考虑生产部署")

        print("=" * 70)


async def main():
    """Main function."""
    print("🏭 Football Data Platform 生产就绪度检查")
    print("=" * 70)

    checker = ProductionChecker()

    # Run all checks
    await checker.check_environment_config()
    await checker.check_api_connectivity()
    await checker.check_database_connectivity()
    await checker.check_redis_connectivity()
    await checker.check_monitoring_setup()
    await checker.check_security_config()

    # Generate and display report
    report = await checker.generate_report()
    checker.print_report(report)

    # Save report
    os.makedirs("data/reports", exist_ok=True)
    with open("data/reports/production_readiness.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n📄 详细报告已保存: data/reports/production_readiness.json")

    # Exit code based on readiness
    return 0 if report["overall_score"] >= 75 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
