#!/usr/bin/env python3
"""
真实数据抓取脚本 - 五大联赛 + 英冠
"""

import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 目标联赛配置 (按优先级排序)
TARGET_LEAGUES = {
    "英超": {"id": 2021, "name": "Premier League", "priority": 1},
    "英冠": {"id": 2016, "name": "Championship", "priority": 1},
    "西甲": {"id": 2014, "name": "Primera Division", "priority": 2},
    "德甲": {"id": 2002, "name": "Bundesliga", "priority": 2},
    "意甲": {"id": 2019, "name": "Serie A", "priority": 2},
    "法甲": {"id": 2015, "name": "Ligue 1", "priority": 2},
}


class RealDataCollector:
    """真实数据收集器"""

    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_DATA_API_KEY")
        self.base_url = "https://api.football-data.org/v4"
        self.db_path = "football_data.db"

        if not self.api_key or self.api_key == "your_football_data_api_key_here":
            raise ValueError("❌ API密钥未配置或无效")

        print(f"✅ API密钥已加载: {self.api_key[:8]}...***")

    def setup_database(self):
        """设置数据库表结构"""
        print("🗄️ 设置数据库...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建比赛表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS real_matches (
                id INTEGER PRIMARY KEY,
                api_id INTEGER UNIQUE,
                league_id INTEGER,
                league_name TEXT,
                season TEXT,
                matchday INTEGER,
                status TEXT,
                utc_date TEXT,
                home_team_id INTEGER,
                home_team_name TEXT,
                away_team_id INTEGER,
                away_team_name TEXT,
                home_score INTEGER,
                away_score INTEGER,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建球队表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS real_teams (
                id INTEGER PRIMARY KEY,
                api_id INTEGER UNIQUE,
                name TEXT,
                short_name TEXT,
                crest TEXT,
                founded INTEGER,
                venue TEXT,
                league_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建收集日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_logs (
                id INTEGER PRIMARY KEY,
                league_name TEXT,
                league_id INTEGER,
                collection_date TEXT,
                matches_collected INTEGER,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        print("✅ 数据库表结构已设置")

    async def collect_league_teams(
        self, session: aiohttp.ClientSession, league_id: int, league_name: str
    ) -> list[dict]:
        """收集联赛球队信息"""

        headers = {"Accept": "application/json", "X-Auth-Token": self.api_key}

        url = f"{self.base_url}/competitions/{league_id}/teams"

        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    teams = data.get("teams", [])
                    print(f"  📊 {league_name}: 获取到 {len(teams)} 支球队")
                    return teams
                await response.text()
                print(f"  ❌ {league_name}: 球队获取失败 ({response.status})")
                return []

        except Exception as e:
            print(f"  ❌ {league_name}: 网络错误 - {e}")
            return []

    async def collect_league_matches(
        self,
        session: aiohttp.ClientSession,
        league_id: int,
        league_name: str,
        days_back: int = 180,
    ) -> list[dict]:
        """收集联赛比赛数据"""

        headers = {"Accept": "application/json", "X-Auth-Token": self.api_key}

        # 计算日期范围 (免费版通常限制6个月)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        params = {
            "dateFrom": start_date.strftime("%Y-%m-%d"),
            "dateTo": end_date.strftime("%Y-%m-%d"),
        }

        url = f"{self.base_url}/competitions/{league_id}/matches"

        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    matches = data.get("matches", [])
                    print(f"  📈 {league_name}: 获取到 {len(matches)} 场比赛")
                    return matches
                error_text = await response.text()
                print(f"  ❌ {league_name}: 比赛获取失败 ({response.status})")
                if "subscription" in error_text.lower():
                    print(f"  💡 {league_name}: 可能需要付费版本访问")
                return []

        except Exception as e:
            print(f"  ❌ {league_name}: 网络错误 - {e}")
            return []

    def save_teams_to_db(self, teams: list[dict], league_id: int):
        """保存球队数据到数据库"""

        if not teams:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0

        for team in teams:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO real_teams
                    (api_id, name, short_name, crest, founded, venue, league_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        team.get("id"),
                        team.get("name"),
                        team.get("shortName"),
                        team.get("crest"),
                        team.get("founded"),
                        team.get("venue"),
                        league_id,
                    ),
                )

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                print(f"    ⚠️ 球队保存错误: {e}")

        conn.commit()
        conn.close()

        return saved_count

    def save_matches_to_db(self, matches: list[dict], league_id: int, league_name: str):
        """保存比赛数据到数据库"""

        if not matches:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0

        for match in matches:
            try:
                # 提取比分
                score = match.get("score", {})
                fulltime = score.get("fullTime", {})
                home_score = fulltime.get("home")
                away_score = fulltime.get("away")

                # 确定结果
                result = None
                if home_score is not None and away_score is not None:
                    if home_score > away_score:
                        result = "H"
                    elif home_score < away_score:
                        result = "A"
                    else:
                        result = "D"

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO real_matches
                    (api_id, league_id, league_name, season, matchday, status,
                     utc_date, home_team_id, home_team_name, away_team_id,
                     away_team_name, home_score, away_score, result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        match.get("id"),
                        league_id,
                        league_name,
                        match.get("season", {}).get("id"),
                        match.get("matchday"),
                        match.get("status"),
                        match.get("utcDate"),
                        match.get("homeTeam", {}).get("id"),
                        match.get("homeTeam", {}).get("name"),
                        match.get("awayTeam", {}).get("id"),
                        match.get("awayTeam", {}).get("name"),
                        home_score,
                        away_score,
                        result,
                    ),
                )

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                print(f"    ⚠️ 比赛保存错误: {e}")

        conn.commit()
        conn.close()

        return saved_count

    def log_collection(
        self,
        league_name: str,
        league_id: int,
        matches_count: int,
        status: str,
        error: str | None = None,
    ):
        """记录收集日志"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO collection_logs
            (league_name, league_id, collection_date, matches_collected, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                league_name,
                league_id,
                datetime.now().strftime("%Y-%m-%d"),
                matches_count,
                status,
                error,
            ),
        )

        conn.commit()
        conn.close()

    async def collect_all_data(self):
        """收集所有数据"""

        print("🚀 开始真实数据收集")
        print("=" * 60)

        # 设置数据库
        self.setup_database()

        async with aiohttp.ClientSession() as session:
            # 按优先级排序
            sorted_leagues = sorted(
                TARGET_LEAGUES.items(), key=lambda x: x[1]["priority"]
            )

            for league_name, league_info in sorted_leagues:
                league_id = league_info["id"]
                priority = league_info["priority"]

                print(
                    f"\n🏆 抓取 {league_name} (ID: {league_id}, Priority: {priority})"
                )
                print("-" * 40)

                try:
                    # 1. 收集球队信息
                    print("  👥 收集球队信息...")
                    teams = await self.collect_league_teams(
                        session, league_id, league_name
                    )
                    teams_saved = self.save_teams_to_db(teams, league_id)
                    print(f"  💾 保存了 {teams_saved} 支球队")

                    # 等待避免速率限制
                    await asyncio.sleep(6)

                    # 2. 收集比赛数据
                    print("  ⚽ 收集比赛数据 (最近6个月)...")
                    matches = await self.collect_league_matches(
                        session, league_id, league_name
                    )
                    matches_saved = self.save_matches_to_db(
                        matches, league_id, league_name
                    )
                    print(f"  💾 保存了 {matches_saved} 场比赛")

                    # 记录成功日志
                    self.log_collection(
                        league_name, league_id, matches_saved, "success"
                    )
                    print(f"  ✅ {league_name} 数据收集完成!")

                except Exception as e:
                    print(f"  ❌ {league_name} 收集失败: {e}")
                    self.log_collection(league_name, league_id, 0, "error", str(e))

                # 联赛间等待时间 (避免速率限制)
                print("  ⏱️ 等待12秒...")
                await asyncio.sleep(12)

        # 生成收集报告
        self.generate_collection_report()

    def generate_collection_report(self):
        """生成数据收集报告"""

        print("\n📋 生成数据收集报告")
        print("=" * 60)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 统计收集结果
        cursor.execute("""
            SELECT league_name, COUNT(*) as match_count
            FROM real_matches
            GROUP BY league_name
        """)
        match_stats = cursor.fetchall()

        cursor.execute("""
            SELECT league_id, COUNT(*) as team_count
            FROM real_teams
            GROUP BY league_id
        """)
        team_stats = cursor.fetchall()

        # 收集日志
        cursor.execute("""
            SELECT * FROM collection_logs
            ORDER BY created_at DESC
            LIMIT 10
        """)
        logs = cursor.fetchall()

        conn.close()

        # 显示统计结果
        print("📊 数据收集统计:")
        total_matches = 0
        total_teams = 0

        for league_name, match_count in match_stats:
            total_matches += match_count
            print(f"  • {league_name}: {match_count} 场比赛")

        team_dict = dict(team_stats)
        for league_name, league_info in TARGET_LEAGUES.items():
            league_id = league_info["id"]
            team_count = team_dict.get(league_id, 0)
            total_teams += team_count
            print(f"  • {league_name}: {team_count} 支球队")

        print("\n🎯 总计:")
        print(f"  • 总比赛数: {total_matches}")
        print(f"  • 总球队数: {total_teams}")

        # 保存详细报告
        report = {
            "收集时间": datetime.now().isoformat(),
            "API版本": "免费版",
            "总比赛数": total_matches,
            "总球队数": total_teams,
            "按联赛统计": dict(match_stats),
            "收集日志": [
                {"联赛": log[1], "状态": log[5], "比赛数": log[4], "时间": log[7]}
                for log in logs
            ],
        }

        report_file = (
            Path("data/analysis_results")
            / f"collection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 详细报告已保存: {report_file}")

        if total_matches > 0:
            print("\n🎉 数据收集成功! 现在可以进行分析了")
        else:
            print("\n⚠️ 未收集到比赛数据,请检查API限制")


async def main():
    """主函数"""

    try:
        collector = RealDataCollector()
        await collector.collect_all_data()

    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("请先运行: python scripts/quick_api_test.py")

    except Exception as e:
        print(f"❌ 收集过程出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())
