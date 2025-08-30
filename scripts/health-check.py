#!/usr/bin/env python3
"""
系统健康检查脚本
检查所有关键组件的运行状态
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict

import httpx
import psycopg2
import redis
import structlog

# 配置日志
logger = structlog.get_logger()


class HealthChecker:
    """系统健康检查器"""

    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.load_config()

    def load_config(self):
        """加载环境配置"""
        from dotenv import load_dotenv

        load_dotenv()

        self.database_url = os.getenv("DATABASE_URL", "")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.prefect_url = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")

    async def check_database(self) -> Dict:
        """检查数据库连接"""
        logger.info("Checking database connection...")

        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            return {
                "status": "healthy",
                "message": "Database connection successful",
                "response_time": 0.1,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {e!s}",
                "response_time": None,
            }

    async def check_redis(self) -> Dict:
        """检查Redis连接"""
        logger.info("Checking Redis connection...")

        try:
            r = redis.from_url(self.redis_url)
            start_time = time.time()
            r.ping()
            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "response_time": response_time,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {e!s}",
                "response_time": None,
            }

    async def check_api(self) -> Dict:
        """检查API服务"""
        logger.info("Checking API service...")

        try:
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                response = await client.get(
                    f"{self.api_url}/api/v1/health", timeout=10.0
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "message": "API service is running",
                        "response_time": response_time,
                        "status_code": response.status_code,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"API returned status {response.status_code}",
                        "response_time": response_time,
                        "status_code": response.status_code,
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"API connection failed: {e!s}",
                "response_time": None,
            }

    async def check_prefect(self) -> Dict:
        """检查Prefect服务"""
        logger.info("Checking Prefect service...")

        try:
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                response = await client.get(f"{self.prefect_url}/health", timeout=10.0)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "message": "Prefect service is running",
                        "response_time": response_time,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Prefect returned status {response.status_code}",
                        "response_time": response_time,
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Prefect connection failed: {e!s}",
                "response_time": None,
            }

    def check_filesystem(self) -> Dict:
        """检查文件系统"""
        logger.info("Checking filesystem...")

        required_dirs = ["logs", "models/artifacts", "data/samples"]

        missing_dirs = []
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            return {
                "status": "unhealthy",
                "message": f"Missing directories: {', '.join(missing_dirs)}",
                "missing_directories": missing_dirs,
            }
        else:
            return {"status": "healthy", "message": "All required directories exist"}

    def check_environment(self) -> Dict:
        """检查环境变量"""
        logger.info("Checking environment variables...")

        required_vars = ["DATABASE_URL", "REDIS_URL", "FOOTBALL_DATA_API_KEY"]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            return {
                "status": "unhealthy",
                "message": f"Missing environment variables: {', '.join(missing_vars)}",
                "missing_variables": missing_vars,
            }
        else:
            return {
                "status": "healthy",
                "message": "All required environment variables are set",
            }

    async def run_all_checks(self) -> Dict:
        """运行所有健康检查"""
        logger.info("Starting comprehensive health check...")

        checks = {
            "database": self.check_database(),
            "redis": self.check_redis(),
            "api": self.check_api(),
            "prefect": self.check_prefect(),
            "filesystem": self.check_filesystem(),
            "environment": self.check_environment(),
        }

        # 执行异步检查
        async_results = await asyncio.gather(
            checks["database"],
            checks["redis"],
            checks["api"],
            checks["prefect"],
            return_exceptions=True,
        )

        # 合并结果
        self.results = {
            "database": async_results[0]
            if not isinstance(async_results[0], Exception)
            else {"status": "error", "message": str(async_results[0])},
            "redis": async_results[1]
            if not isinstance(async_results[1], Exception)
            else {"status": "error", "message": str(async_results[1])},
            "api": async_results[2]
            if not isinstance(async_results[2], Exception)
            else {"status": "error", "message": str(async_results[2])},
            "prefect": async_results[3]
            if not isinstance(async_results[3], Exception)
            else {"status": "error", "message": str(async_results[3])},
            "filesystem": checks["filesystem"],
            "environment": checks["environment"],
        }

        # 计算总体状态
        overall_status = "healthy"
        unhealthy_services = []

        for service, result in self.results.items():
            if result["status"] != "healthy":
                overall_status = "unhealthy"
                unhealthy_services.append(service)

        return {
            "timestamp": time.time(),
            "overall_status": overall_status,
            "unhealthy_services": unhealthy_services,
            "services": self.results,
        }

    def print_results(self, results: Dict):
        """打印检查结果"""
        print("\n" + "=" * 60)
        print("🏥 SYSTEM HEALTH CHECK REPORT")
        print("=" * 60)

        # 总体状态
        status_emoji = "✅" if results["overall_status"] == "healthy" else "❌"
        print(f"\n{status_emoji} Overall Status: {results['overall_status'].upper()}")

        if results["unhealthy_services"]:
            print(f"❌ Unhealthy Services: {', '.join(results['unhealthy_services'])}")

        print("\n" + "-" * 60)
        print("SERVICE DETAILS")
        print("-" * 60)

        for service, result in results["services"].items():
            status_emoji = "✅" if result["status"] == "healthy" else "❌"
            print(f"\n{status_emoji} {service.upper()}")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")

            if "response_time" in result and result["response_time"] is not None:
                print(f"   Response Time: {result['response_time']:.3f}s")

        print("\n" + "=" * 60)


async def main():
    """主函数"""
    checker = HealthChecker()
    results = await checker.run_all_checks()

    # 打印结果
    checker.print_results(results)

    # 保存结果到文件
    with open("health-check-results.json", "w") as f:
        json.dump(results, f, indent=2)

    # 根据结果设置退出码
    exit_code = 0 if results["overall_status"] == "healthy" else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
