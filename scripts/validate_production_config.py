#!/usr/bin/env python3
"""
🔐 生产环境配置安全验证脚本

在生产部署前运行此脚本来验证配置安全性。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from football_predict_system.core.config import get_settings
except ImportError:
    print("❌ 无法导入配置模块, 请确保在项目根目录运行")
    sys.exit(1)


def check_secret_security(secret_key: str) -> list[str]:
    """检查密钥安全性。"""
    issues = []

    # 检查默认值
    default_keys = [
        "your-super-secret-key-change-in-production",
        "dev-secret-key-not-for-production",
        "test_secret",
        "secret_key",
    ]

    if secret_key.lower() in [k.lower() for k in default_keys]:
        issues.append("Using default/demo secret key")

    # 检查长度
    if len(secret_key) < 32:
        issues.append(f"Secret key too short: {len(secret_key)} chars (minimum: 32)")

        # 检查复杂度
    if secret_key.isalnum() and len(secret_key) < 64:
        issues.append("Secret key lacks complexity (consider adding symbols)")

    return issues


def check_cors_security(cors_origins: list[str]) -> list[str]:
    """检查CORS配置安全性。"""
    issues = []

    if "*" in cors_origins:
        issues.append("CORS allows all origins (*) - security risk")

    if "http://localhost" in str(cors_origins):
        issues.append("CORS includes localhost - remove for production")

    if not cors_origins or len(cors_origins) == 0:
        issues.append("CORS origins not configured")

    return issues


def check_database_security(db_url: str) -> list[str]:
    """检查数据库配置安全性。"""
    issues = []

    # 检查弱密码
    weak_passwords = ["password", "123456", "admin", "test", "root"]
    for weak_pwd in weak_passwords:
        if f":{weak_pwd}@" in db_url:
            issues.append(f"Database uses weak password: {weak_pwd}")

    # 检查协议
    if db_url.startswith("sqlite://"):
        issues.append("Using SQLite in production (consider PostgreSQL)")

    return issues


def main() -> int:
    """主验证函数。"""
    print("🔐 生产环境配置安全验证")
    print("=" * 50)

    try:
        # 设置生产环境标识
        os.environ["ENVIRONMENT"] = "production"
        settings = get_settings()

        all_issues = []

        # 1. 检查密钥安全
        print("🔑 检查密钥配置...")
        secret_issues = check_secret_security(settings.api.secret_key)
        all_issues.extend([f"Secret: {issue}" for issue in secret_issues])

        # 2. 检查CORS配置
        print("🌐 检查CORS配置...")
        cors_issues = check_cors_security(settings.api.cors_origins)
        all_issues.extend([f"CORS: {issue}" for issue in cors_issues])

        # 3. 检查数据库配置
        print("🗄️ 检查数据库配置...")
        db_issues = check_database_security(settings.get_database_url())
        all_issues.extend([f"Database: {issue}" for issue in db_issues])

        # 4. 检查调试模式
        print("🐛 检查调试设置...")
        if settings.debug:
            all_issues.append("Debug: Debug mode is enabled")

        # 5. 检查环境变量
        print("🌍 检查环境变量...")
        required_env_vars = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"]

        for var in required_env_vars:
            if not os.getenv(var):
                all_issues.append(f"Environment: Missing {var}")

        # 输出结果
        print("\n" + "=" * 50)
        if all_issues:
            print("❌ 发现安全问题:")
            for issue in all_issues:
                print(f"  • {issue}")
            print(f"\n总计: {len(all_issues)} 个安全问题")
            print("\n🚨 不建议部署到生产环境!")
            print("请修复上述问题后重新验证。")
            return 1
        else:
            print("✅ 所有安全检查通过!")
            print("🚀 配置满足生产环境部署要求。")
            return 0

    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
