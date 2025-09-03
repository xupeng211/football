#!/usr/bin/env python3
"""
批量抓取五大联赛和英冠联赛数据
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 目标联赛配置
TARGET_LEAGUES = {
    "英超": {"id": 2021, "name": "Premier League", "country": "England"},
    "西甲": {"id": 2014, "name": "Primera Division", "country": "Spain"},
    "德甲": {"id": 2002, "name": "Bundesliga", "country": "Germany"},
    "意甲": {"id": 2019, "name": "Serie A", "country": "Italy"},
    "法甲": {"id": 2015, "name": "Ligue 1", "country": "France"},
    "英冠": {"id": 2016, "name": "Championship", "country": "England"},
}


class FootballDataCollector:
    """免费版Football-Data.org数据收集器"""

    def __init__(self, api_key: str | None = None):
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {"Accept": "application/json"}
        if api_key:
            self.headers["X-Auth-Token"] = api_key

        # 免费版限制:每分钟10次请求
        self.request_delay = 6  # 秒

    async def fetch_teams(self, competition_id: int) -> list[dict[str, Any]]:
        """获取联赛的球队数据"""

        url = f"{self.base_url}/competitions/{competition_id}/teams"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        teams = data.get("teams", [])
                        print(f"  📍 获取到 {len(teams)} 支球队")
                        return teams
                    print(f"  ❌ 球队数据获取失败: {response.status}")
                    return []

            except Exception as e:
                print(f"  ❌ 网络错误: {e}")
                return []

    async def fetch_matches(
        self, competition_id: int, days_back: int = 30
    ) -> list[dict[str, Any]]:
        """获取联赛的比赛数据"""

        # 计算日期范围 - 最近30天
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        date_from = start_date.strftime("%Y-%m-%d")
        date_to = end_date.strftime("%Y-%m-%d")

        url = f"{self.base_url}/competitions/{competition_id}/matches"
        params = {"dateFrom": date_from, "dateTo": date_to}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url, headers=self.headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches = data.get("matches", [])
                        print(
                            f"  📊 获取到 {len(matches)} 场比赛 ({date_from} 到 {date_to})"
                        )
                        return matches
                    print(f"  ❌ 比赛数据获取失败: {response.status}")
                    error_text = await response.text()
                    print(f"  错误详情: {error_text[:200]}")
                    return []

            except Exception as e:
                print(f"  ❌ 网络错误: {e}")
                return []

    async def collect_league_data(
        self, league_name: str, competition_id: int
    ) -> dict[str, Any]:
        """收集单个联赛的完整数据"""

        print(f"\n🏆 开始收集 {league_name} (ID: {competition_id}) 数据...")

        # 先收集球队数据
        teams = await self.fetch_teams(competition_id)
        await asyncio.sleep(self.request_delay)  # 速率限制

        # 再收集比赛数据
        matches = await self.fetch_matches(competition_id)
        await asyncio.sleep(self.request_delay)  # 速率限制

        result = {
            "league_name": league_name,
            "competition_id": competition_id,
            "teams": teams,
            "matches": matches,
            "teams_count": len(teams),
            "matches_count": len(matches),
            "collected_at": datetime.utcnow().isoformat(),
        }

        print(
            f"  ✅ {league_name} 数据收集完成: {len(teams)} 球队, {len(matches)} 比赛"
        )
        return result


async def collect_all_leagues() -> list[dict[str, Any]]:
    """收集所有目标联赛的数据"""

    collector = FootballDataCollector()  # 使用免费版,无需API密钥
    all_results = []

    print("🚀 开始批量收集联赛数据...")
    print(f"🎯 目标联赛: {', '.join(TARGET_LEAGUES.keys())}")

    for league_name, league_info in TARGET_LEAGUES.items():
        try:
            result = await collector.collect_league_data(league_name, league_info["id"])
            all_results.append(result)

        except Exception as e:
            print(f"❌ {league_name} 数据收集失败: {e}")

        # 联赛间暂停,避免超出速率限制
        print("  ⏰ 等待6秒避免速率限制...")
        await asyncio.sleep(6)

    return all_results


def save_results_to_files(results: list[dict[str, Any]]) -> None:
    """保存结果到文件"""

    # 创建数据目录
    data_dir = Path("data/collected")
    data_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for result in results:
        league_name = result["league_name"]

        # 保存球队数据
        if result["teams"]:
            teams_df = pd.DataFrame(result["teams"])
            teams_file = data_dir / f"{league_name}_teams_{timestamp}.csv"
            teams_df.to_csv(teams_file, index=False, encoding="utf-8")
            print(f"💾 {league_name} 球队数据已保存: {teams_file}")

        # 保存比赛数据
        if result["matches"]:
            matches_df = pd.DataFrame(result["matches"])
            matches_file = data_dir / f"{league_name}_matches_{timestamp}.csv"
            matches_df.to_csv(matches_file, index=False, encoding="utf-8")
            print(f"💾 {league_name} 比赛数据已保存: {matches_file}")

    # 保存汇总报告
    summary = {
        "收集时间": timestamp,
        "联赛数量": len(results),
        "详细统计": [
            {
                "联赛": r["league_name"],
                "联赛ID": r["competition_id"],
                "球队数": r["teams_count"],
                "比赛数": r["matches_count"],
            }
            for r in results
        ],
    }

    summary_file = data_dir / f"collection_summary_{timestamp}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n📋 汇总报告已保存: {summary_file}")


async def main():
    """主函数"""

    print("⚽ 足球数据抓取工具 - 五大联赛 + 英冠")
    print("=" * 60)

    # 收集数据
    results = await collect_all_leagues()

    if results:
        print("\n" + "=" * 60)
        print("📊 数据收集汇总:")

        total_teams = sum(r["teams_count"] for r in results)
        total_matches = sum(r["matches_count"] for r in results)

        print(
            f"📈 总计: {len(results)} 个联赛, {total_teams} 支球队, {total_matches} 场比赛"
        )

        for result in results:
            print(
                f"  • {result['league_name']}: {result['teams_count']} 球队, {result['matches_count']} 比赛"
            )

        # 保存到文件
        save_results_to_files(results)

        print("\n🎉 数据抓取完成!数据已保存到 data/collected/ 目录")

    else:
        print("\n❌ 没有成功收集到任何数据")


if __name__ == "__main__":
    asyncio.run(main())
