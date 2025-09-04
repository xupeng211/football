#!/usr/bin/env python3
"""
本地CI数据库测试脚本
===========================

这个脚本模拟CI环境中的数据库测试, 帮助开发者在提交代码前发现数据库相关问题。

特性:  # noqa: RUF002
- 模拟CI环境的SQLite数据库初始化
- 测试关键数据库功能
- 验证schema完整性
- 检查数据平台核心功能

使用方法:  # noqa: RUF002
    python scripts/local_ci_db_test.py
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def setup_test_database() -> str:
    """设置测试数据库，返回数据库文件路径"""  # noqa: RUF002
    print("🏗️ 设置测试SQLite数据库...")

    # 创建临时数据库文件
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_football_ci.db")

    # 读取schema文件
    schema_file = project_root / "sql" / "schema_sqlite.sql"
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema文件不存在: {schema_file}")

    with open(schema_file, encoding="utf-8") as f:
        schema_sql = f.read()

    # 初始化数据库
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

    print(f"✅ SQLite数据库初始化完成: {db_path}")
    return db_path


def verify_schema_integrity(db_path: str) -> None:
    """验证数据库schema完整性"""
    print("🔍 验证数据库schema完整性...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查必要的表是否存在
    required_tables = ["teams", "matches", "data_sources", "data_collection_logs"]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]

    for table in required_tables:
        if table not in existing_tables:
            raise AssertionError(f"❌ 缺少必要的表: {table}")
        print(f"  ✅ 表 '{table}' 存在")

    # 检查data_sources表的结构
    cursor.execute("PRAGMA table_info(data_sources)")
    columns = [row[1] for row in cursor.fetchall()]
    required_columns = ["id", "name", "source_type"]

    for col in required_columns:
        if col not in columns:
            raise AssertionError(f"❌ data_sources表缺少列: {col}")

    conn.close()
    print("✅ Schema完整性验证通过")


async def test_database_writer(db_path: str) -> None:
    """测试DatabaseWriter核心功能"""
    print("🧪 测试DatabaseWriter核心功能...")

    # 设置环境变量使用测试数据库
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    from football_predict_system.data_platform.sources.base import CollectionStats
    from football_predict_system.data_platform.storage.database_writer import (
        DatabaseWriter,
    )
    from football_predict_system.domain.models import Team

    writer = DatabaseWriter()

    # 1. 测试团队写入
    print("  📝 测试团队数据写入...")
    test_teams = [
        Team(external_api_id=100, name="Test Team A", short_name="TTA", tla="TTA"),
        Team(external_api_id=101, name="Test Team B", short_name="TTB", tla="TTB"),
    ]

    result = await writer.upsert_teams(test_teams)
    expected = 2
    actual = result.records_processed
    assert actual == expected, f"团队写入失败: 期望{expected}, 实际{actual}"
    print("    ✅ 团队数据写入成功")

    # 2. 测试数据质量统计
    print("  📊 测试数据质量统计...")
    stats = await writer.get_data_quality_stats()
    assert "total_matches" in stats, "数据质量统计缺少total_matches"
    assert "teams_count" in stats, "数据质量统计缺少teams_count"
    print("    ✅ 数据质量统计正常")

    # 3. 测试日志记录功能 (这是CI失败的关键测试)
    print("  📝 测试采集日志记录...")
    collection_stats = CollectionStats(
        started_at=datetime.utcnow(), records_fetched=10, records_processed=8
    )

    try:
        await writer.log_collection_run(
            "test_source", "local_ci_test", collection_stats.model_dump()
        )
        print("    ✅ 采集日志记录成功")
    except Exception as e:
        raise AssertionError(f"❌ 采集日志记录失败: {e}")

    print("✅ DatabaseWriter功能测试通过")


async def test_api_data_parsing() -> None:
    """测试API数据解析功能"""
    print("🔄 测试API数据解析功能...")

    from football_predict_system.data_platform.sources.football_data_api import (
        FootballDataAPICollector,
    )

    collector = FootballDataAPICollector(api_key="test_key")

    # 模拟API响应数据
    mock_matches_response = {
        "matches": [
            {
                "id": 1,
                "homeTeam": {
                    "id": 1,
                    "name": "Liverpool",
                    "shortName": "LIV",
                    "tla": "LIV",
                },
                "awayTeam": {
                    "id": 2,
                    "name": "Arsenal",
                    "shortName": "ARS",
                    "tla": "ARS",
                },
                "utcDate": "2024-01-01T15:00:00Z",
                "score": {"fullTime": {"home": 2, "away": 1}},
                "status": "FINISHED",
            }
        ]
    }

    # 测试数据解析
    matches_df = collector._parse_matches_response(mock_matches_response)
    assert len(matches_df) == 1, "应该解析出1场比赛"
    assert matches_df.iloc[0]["home_score"] == 2, "主队得分应该是2"
    assert matches_df.iloc[0]["away_score"] == 1, "客队得分应该是1"

    print("✅ API数据解析测试通过")


def cleanup_test_database(db_path: str) -> None:
    """清理测试数据库"""
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            os.rmdir(os.path.dirname(db_path))
        print("🧹 测试数据库已清理")
    except Exception as e:
        print(f"⚠️ 清理测试数据库时出现警告: {e}")


async def main():
    """主测试流程"""
    print("🚀 开始本地CI数据库测试")
    print("=" * 50)

    db_path = None
    try:
        # 1. 设置测试数据库
        db_path = setup_test_database()

        # 2. 验证schema完整性
        verify_schema_integrity(db_path)

        # 3. 测试数据库写入功能
        await test_database_writer(db_path)

        # 4. 测试API数据解析
        await test_api_data_parsing()

        print("=" * 50)
        print("🎉 所有本地CI数据库测试通过!")
        print("✅ 代码可以安全提交到远程仓库")
        return True

    except Exception as e:
        print("=" * 50)
        print(f"❌ 本地CI数据库测试失败: {e}")
        print("🚫 请修复问题后再提交代码")
        return False

    finally:
        # 清理测试数据库
        if db_path:
            cleanup_test_database(db_path)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
