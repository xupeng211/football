#!/usr/bin/env python3
"""
足球预测系统综合测试套件
"""

import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import aiohttp

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class FootballSystemTester:
    """足球预测系统测试器"""

    def __init__(self):
        self.db_path = "football_data.db"
        self.api_key = os.getenv("FOOTBALL_DATA_API_KEY")
        self.test_results = {}
        self.issues = []

    def run_all_tests(self):
        """运行所有测试"""

        print("🧪 足球预测系统综合测试")
        print("=" * 60)

        tests = [
            ("数据库连接测试", self.test_database_connection),
            ("数据完整性测试", self.test_data_integrity),
            ("API连接测试", self.test_api_connection),
            ("系统功能测试", self.test_system_functions),
            ("预测模型测试", self.test_prediction_capability),
            ("性能压力测试", self.test_performance),
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            print(f"\n{'=' * 20} {test_name} {'=' * 20}")

            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = asyncio.run(test_func())
                else:
                    result = test_func()

                if result:
                    print(f"✅ {test_name} - 通过")
                    passed_tests += 1
                else:
                    print(f"❌ {test_name} - 失败")

            except Exception as e:
                print(f"💥 {test_name} - 异常: {e}")
                self.issues.append(f"{test_name}: {e!s}")

        # 生成测试报告
        self.generate_test_report(passed_tests, total_tests)

        return passed_tests, total_tests

    def test_database_connection(self):
        """测试数据库连接"""

        print("🗄️ 测试数据库连接...")

        try:
            # 检查文件存在
            if not os.path.exists(self.db_path):
                self.issues.append("数据库文件不存在")
                return False

            # 连接测试
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ["real_matches", "real_teams", "collection_logs"]
            missing_tables = [t for t in required_tables if t not in tables]

            if missing_tables:
                self.issues.append(f"缺少数据表: {missing_tables}")
                return False

            print("  ✅ 数据库连接正常")
            print(f"  ✅ 必需表存在: {required_tables}")

            conn.close()
            return True

        except Exception as e:
            self.issues.append(f"数据库连接错误: {e}")
            return False

    def test_data_integrity(self):
        """测试数据完整性"""

        print("📊 测试数据完整性...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查数据量
            cursor.execute("SELECT COUNT(*) FROM real_matches")
            match_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM real_teams")
            team_count = cursor.fetchone()[0]

            print(f"  📈 比赛数据: {match_count} 场")
            print(f"  👥 球队数据: {team_count} 支")

            # 数据质量检查
            cursor.execute("""
                SELECT COUNT(*) FROM real_matches
                WHERE home_team_name IS NULL OR away_team_name IS NULL
            """)
            missing_teams = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM real_matches
                WHERE utc_date IS NULL
            """)
            missing_dates = cursor.fetchone()[0]

            # 数据量阈值检查
            data_sufficient = match_count >= 500 and team_count >= 80
            data_quality_good = missing_teams == 0 and missing_dates == 0

            if not data_sufficient:
                self.issues.append(
                    f"数据量不足: {match_count}场比赛, {team_count}支球队"
                )

            if not data_quality_good:
                self.issues.append(
                    f"数据质量问题: {missing_teams}缺失球队, {missing_dates}缺失日期"
                )

            print(f"  ✅ 数据量充足: {data_sufficient}")
            print(f"  ✅ 数据质量良好: {data_quality_good}")

            conn.close()
            return data_sufficient and data_quality_good

        except Exception as e:
            self.issues.append(f"数据完整性检查错误: {e}")
            return False

    async def test_api_connection(self):
        """测试API连接"""

        print("🌐 测试API连接...")

        if not self.api_key or self.api_key == "your_football_data_api_key_here":
            self.issues.append("API密钥未配置")
            return False

        try:
            base_url = "https://api.football-data.org/v4"
            headers = {"Accept": "application/json", "X-Auth-Token": self.api_key}

            async with aiohttp.ClientSession() as session:
                # 测试基本连接
                async with session.get(
                    f"{base_url}/competitions", headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        comp_count = len(data.get("competitions", []))
                        print("  ✅ API连接正常")
                        print(f"  ✅ 可访问 {comp_count} 个联赛")
                        return True
                    else:
                        error_text = await response.text()
                        self.issues.append(
                            f"API请求失败: {response.status} - {error_text[:100]}"
                        )
                        return False

        except Exception as e:
            self.issues.append(f"API连接错误: {e}")
            return False

    def test_system_functions(self):
        """测试系统功能"""

        print("⚙️ 测试系统功能...")

        try:
            # 测试数据查询功能
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 1. 测试联赛统计查询
            cursor.execute("""
                SELECT league_name, COUNT(*) as match_count,
                       AVG(CASE WHEN home_score IS NOT NULL AND away_score IS NOT NULL
                           THEN home_score + away_score END) as avg_goals
                FROM real_matches
                GROUP BY league_name
                HAVING match_count > 10
            """)
            league_stats = cursor.fetchall()

            if len(league_stats) < 4:  # 至少4个联赛有足够数据
                self.issues.append("活跃联赛数量不足")
                return False

            print(f"  ✅ 联赛统计查询正常: {len(league_stats)} 个活跃联赛")

            # 2. 测试时间范围查询
            cursor.execute("""
                SELECT COUNT(*) FROM real_matches
                WHERE utc_date >= date('now', '-30 days')
            """)
            recent_matches = cursor.fetchone()[0]

            print(f"  ✅ 时间查询正常: 最近30天 {recent_matches} 场比赛")

            # 3. 测试联表查询
            cursor.execute("""
                SELECT m.league_name, t.name as team_name, COUNT(*) as matches
                FROM real_matches m
                JOIN real_teams t ON m.home_team_id = t.api_id OR m.away_team_id = t.api_id
                GROUP BY m.league_name, t.name
                LIMIT 5
            """)
            join_results = cursor.fetchall()

            if len(join_results) > 0:
                print(f"  ✅ 联表查询正常: {len(join_results)} 条结果")
            else:
                self.issues.append("联表查询失败")
                conn.close()
                return False

            conn.close()
            return True

        except Exception as e:
            self.issues.append(f"系统功能测试错误: {e}")
            return False

    def test_prediction_capability(self):
        """测试预测能力"""

        print("🔮 测试预测能力...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查是否有足够的历史数据进行预测
            cursor.execute("""
                SELECT COUNT(*) FROM real_matches
                WHERE status = 'FINISHED'
                AND home_score IS NOT NULL
                AND away_score IS NOT NULL
            """)
            finished_matches = cursor.fetchone()[0]

            # 检查是否有未来比赛可以预测
            cursor.execute("""
                SELECT COUNT(*) FROM real_matches
                WHERE status IN ('SCHEDULED', 'TIMED')
            """)
            future_matches = cursor.fetchone()[0]

            print(f"  📊 训练数据: {finished_matches} 场已完成比赛")
            print(f"  🔮 待预测: {future_matches} 场未来比赛")

            # 简单的预测逻辑测试
            if finished_matches >= 100:
                # 计算主场胜率作为基础预测
                cursor.execute("""
                    SELECT
                        SUM(CASE WHEN result = 'H' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as home_win_rate
                    FROM real_matches
                    WHERE status = 'FINISHED'
                """)
                home_win_rate = cursor.fetchone()[0]

                print(f"  🏠 历史主场胜率: {home_win_rate:.1%}")

                # 测试基础预测逻辑
                prediction_ready = finished_matches >= 100 and future_matches > 0
                print(f"  ✅ 预测系统ready: {prediction_ready}")

                conn.close()
                return prediction_ready
            else:
                self.issues.append("训练数据不足,无法进行预测")
                conn.close()
                return False

        except Exception as e:
            self.issues.append(f"预测能力测试错误: {e}")
            return False

    def test_performance(self):
        """测试性能"""

        print("⚡ 测试系统性能...")

        try:
            import time

            # 测试数据库查询性能
            start_time = time.time()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 执行复杂查询测试
            cursor.execute("""
                SELECT league_name, home_team_name, away_team_name,
                       home_score, away_score, utc_date
                FROM real_matches
                WHERE status = 'FINISHED'
                ORDER BY utc_date DESC
                LIMIT 100
            """)

            results = cursor.fetchall()
            query_time = time.time() - start_time

            print(f"  ⚡ 查询100条记录耗时: {query_time:.3f}秒")

            # 性能基准
            performance_good = query_time < 1.0 and len(results) > 0

            if not performance_good:
                self.issues.append(f"查询性能较慢: {query_time:.3f}秒")

            print(f"  ✅ 查询性能良好: {performance_good}")

            conn.close()
            return performance_good

        except Exception as e:
            self.issues.append(f"性能测试错误: {e}")
            return False

    def test_data_analysis_functions(self):
        """测试数据分析功能"""

        print("📈 测试数据分析功能...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 测试各种分析查询
            analysis_tests = [
                (
                    "联赛统计",
                    """
                    SELECT league_name, COUNT(*) as matches,
                           AVG(home_score + away_score) as avg_goals
                    FROM real_matches
                    WHERE status = 'FINISHED'
                    GROUP BY league_name
                """,
                ),
                (
                    "主场优势分析",
                    """
                    SELECT league_name,
                           SUM(CASE WHEN result = 'H' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as home_rate
                    FROM real_matches
                    WHERE status = 'FINISHED'
                    GROUP BY league_name
                """,
                ),
                (
                    "时间趋势分析",
                    """
                    SELECT DATE(utc_date) as match_date, COUNT(*) as daily_matches
                    FROM real_matches
                    WHERE utc_date IS NOT NULL
                    GROUP BY DATE(utc_date)
                    ORDER BY match_date DESC
                    LIMIT 10
                """,
                ),
            ]

            analysis_passed = 0

            for test_name, query in analysis_tests:
                try:
                    cursor.execute(query)
                    results = cursor.fetchall()

                    if len(results) > 0:
                        print(f"  ✅ {test_name}: {len(results)} 条结果")
                        analysis_passed += 1
                    else:
                        print(f"  ❌ {test_name}: 无结果")
                        self.issues.append(f"{test_name}查询无结果")

                except Exception as e:
                    print(f"  ❌ {test_name}: {e}")
                    self.issues.append(f"{test_name}查询错误: {e}")

            conn.close()

            success = analysis_passed == len(analysis_tests)
            print(f"  🎯 分析功能通过率: {analysis_passed}/{len(analysis_tests)}")

            return success

        except Exception as e:
            self.issues.append(f"分析功能测试错误: {e}")
            return False

    def generate_test_report(self, passed, total):
        """生成测试报告"""

        print("\n📋 测试结果报告")
        print("=" * 60)

        success_rate = (passed / total) * 100

        print(f"🎯 测试通过率: {passed}/{total} ({success_rate:.1f}%)")

        if self.issues:
            print("\n❌ 发现的问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ 没有发现问题!")

        # 保存详细报告
        report = {
            "测试时间": datetime.now().isoformat(),
            "通过率": f"{success_rate:.1f}%",
            "通过测试": passed,
            "总测试数": total,
            "发现问题": self.issues,
            "建议": self.generate_recommendations(success_rate),
        }

        report_file = (
            Path("data/analysis_results")
            / f"system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 详细报告已保存: {report_file}")

        # 提供修复建议
        if self.issues:
            print("\n🔧 修复建议:")
            self.provide_fix_suggestions()

    def generate_recommendations(self, success_rate):
        """生成改进建议"""

        if success_rate >= 90:
            return ["系统运行良好", "可以开始生产使用", "建议添加监控机制"]
        elif success_rate >= 70:
            return ["系统基本正常", "需要修复部分问题", "建议增加错误处理"]
        else:
            return ["系统存在重要问题", "需要全面检查和修复", "暂不建议生产使用"]

    def provide_fix_suggestions(self):
        """提供修复建议"""

        for issue in self.issues:
            if "API" in issue:
                print("  🔑 API问题: 检查密钥配置和网络连接")
            elif "数据库" in issue:
                print("  🗄️ 数据库问题: 检查文件权限和表结构")
            elif "数据" in issue:
                print("  📊 数据问题: 重新运行数据收集脚本")
            else:
                print("  🔧 其他问题: 检查系统依赖和配置")


def main():
    """主函数"""

    tester = FootballSystemTester()
    passed, total = tester.run_all_tests()

    print("\n🎯 测试完成总结:")

    if passed == total:
        print("🎉 所有测试通过! 系统运行完美!")
        print("✅ 您的足球预测系统已ready for action!")
    elif passed >= total * 0.8:
        print("⚠️ 大部分测试通过,有少量问题需要修复")
        print("🔧 建议先修复问题再继续")
    else:
        print("❌ 发现多个重要问题,需要全面检查")
        print("🚨 建议先解决关键问题")


if __name__ == "__main__":
    main()
