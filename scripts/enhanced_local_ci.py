#!/usr/bin/env python3
"""
增强版本地CI检查 - 完全模拟远程CI环境
解决"本地通过但CI失败"的问题
"""

import os
import subprocess


def set_ci_environment():
    """设置CI环境变量"""
    print("🔧 设置CI环境变量...")
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///./test_football.db"
    os.environ["CI"] = "true"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["FOOTBALL_DATA_API_KEY"] = "test_api_key"
    print("✅ CI环境变量已设置")

def run_command(cmd: str, description: str) -> bool:
    """运行命令并返回是否成功"""
    print(f"\n🔄 {description}...")
    print(f"📝 命令: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - 成功")
        if result.stdout:
            print(f"📄 输出: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - 失败")
        print(f"💬 错误: {e.stderr.strip()}")
        if e.stdout:
            print(f"📄 输出: {e.stdout.strip()}")
        return False

def main():
    """主函数"""
    print("🎭 增强版本地CI检查启动")
    print("=" * 50)
    print("🎯 目标: 完全模拟远程CI环境,确保本地=CI一致")
    print("=" * 50)

    # 设置CI环境
    set_ci_environment()

    # 检查步骤(严格按照CI顺序)
    checks = [
        # 1. 基础代码质量检查
        ("uv run ruff check .", "Ruff代码检查"),
        ("uv run mypy .", "MyPy类型检查"),

        # 2. CI专有的严格模块导入测试
        ("uv run python scripts/ci_database_test.py", "CI友好数据库测试"),

        # 3. 配置系统测试
        ('''uv run python -c "
import sys
sys.path.insert(0, 'src')
from football_predict_system.data_platform.config import get_data_platform_config
config = get_data_platform_config()
assert config.football_data_org.rate_limit_per_minute > 0
print('✅ 配置系统验证通过')
"''', "配置系统验证"),

        # 4. 测试执行
        ("uv run pytest --maxfail=1 --disable-warnings -q", "测试执行"),
    ]

    failed_checks = []

    for cmd, description in checks:
        if not run_command(cmd, description):
            failed_checks.append(description)

    # 结果总结
    print("\n" + "=" * 50)
    print("📊 增强版CI检查结果")
    print("=" * 50)

    if not failed_checks:
        print("🎉 所有检查通过!本地环境与CI完全一致")
        print("✅ 可以安全推送到远程仓库")
        return 0
    else:
        print(f"❌ 发现 {len(failed_checks)} 个问题:")
        for i, check in enumerate(failed_checks, 1):
            print(f"  {i}. {check}")
        print("\n💡 修复建议:")
        print("  1. 运行 'make format lint' 修复代码问题")
        print("  2. 检查类型注解和导入语句")
        print("  3. 确保所有测试通过")
        return 1

if __name__ == "__main__":
    exit(main())
