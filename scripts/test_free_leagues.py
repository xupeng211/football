#!/usr/bin/env python3
"""
测试免费版API可以访问的联赛
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

import aiohttp

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 从第一次查询获取的所有联赛ID (免费版可见的)
FREE_TIER_LEAGUES = [
    {"id": 2021, "name": "Premier League", "country": "England"},
    {"id": 2016, "name": "Championship", "country": "England"},
    {"id": 2002, "name": "Bundesliga", "country": "Germany"},
    {"id": 2019, "name": "Serie A", "country": "Italy"},
    {"id": 2015, "name": "Ligue 1", "country": "France"},
    {"id": 2014, "name": "Primera Division", "country": "Spain"},
    {"id": 2001, "name": "UEFA Champions League", "country": "Europe"},
    {"id": 2018, "name": "European Championship", "country": "Europe"},
    {"id": 2003, "name": "Eredivisie", "country": "Netherlands"},
    {"id": 2017, "name": "Primeira Liga", "country": "Portugal"},
    {"id": 2013, "name": "Campeonato Brasileiro Série A", "country": "Brazil"},
    {"id": 2000, "name": "FIFA World Cup", "country": "World"}
]


async def test_league_access(league_info: dict[str, Any]) -> dict[str, Any]:
    """测试单个联赛的访问权限"""

    base_url = "https://api.football-data.org/v4"
    headers = {"Accept": "application/json"}

    league_id = league_info["id"]
    league_name = league_info["name"]

    print(f"🔍 测试 {league_name} (ID: {league_id})...")

    result = {
        "league_info": league_info,
        "teams_accessible": False,
        "matches_accessible": False,
        "teams_count": 0,
        "recent_matches_count": 0,
        "error_message": None
    }

    async with aiohttp.ClientSession() as session:
        # 测试球队数据访问
        try:
            teams_url = f"{base_url}/competitions/{league_id}/teams"
            async with session.get(teams_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    teams = data.get("teams", [])
                    result["teams_accessible"] = True
                    result["teams_count"] = len(teams)
                    print(f"  ✅ 球队数据可访问: {len(teams)} 支球队")
                else:
                    error_text = await response.text()
                    print(f"  ❌ 球队数据不可访问: {response.status}")
                    result["error_message"] = error_text[:100]
        except Exception as e:
            print(f"  ❌ 球队数据测试失败: {e}")
            result["error_message"] = str(e)

        await asyncio.sleep(6)  # 速率限制

        # 测试比赛数据访问
        try:
            matches_url = f"{base_url}/competitions/{league_id}/matches"
            async with session.get(matches_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    matches = data.get("matches", [])
                    result["matches_accessible"] = True
                    result["recent_matches_count"] = len(matches)
                    print(f"  ✅ 比赛数据可访问: {len(matches)} 场比赛")
                else:
                    error_text = await response.text()
                    print(f"  ❌ 比赛数据不可访问: {response.status}")
                    if not result["error_message"]:
                        result["error_message"] = error_text[:100]
        except Exception as e:
            print(f"  ❌ 比赛数据测试失败: {e}")
            if not result["error_message"]:
                result["error_message"] = str(e)

    return result


async def main():
    """主函数"""

    print("🔍 测试免费版API可访问的联赛")
    print("=" * 60)

    accessible_leagues = []
    restricted_leagues = []

    for i, league_info in enumerate(FREE_TIER_LEAGUES):
        result = await test_league_access(league_info)

        if result["teams_accessible"] or result["matches_accessible"]:
            accessible_leagues.append(result)
        else:
            restricted_leagues.append(result)

        # 避免超出速率限制
        if i < len(FREE_TIER_LEAGUES) - 1:
            print("  ⏰ 等待6秒...")
            await asyncio.sleep(6)

    print("\n" + "=" * 60)
    print("📊 访问权限测试结果:")

    print(f"\n✅ 可访问的联赛 ({len(accessible_leagues)} 个):")
    for result in accessible_leagues:
        info = result["league_info"]
        teams = result["teams_count"]
        matches = result["recent_matches_count"]
        print(f"  • {info['name']} (ID: {info['id']}) - {teams} 球队, {matches} 比赛")

    print(f"\n❌ 受限制的联赛 ({len(restricted_leagues)} 个):")
    for result in restricted_leagues:
        info = result["league_info"]
        print(f"  • {info['name']} (ID: {info['id']}) - 需要付费订阅")

    # 保存可访问联赛的配置
    if accessible_leagues:
        import json

        accessible_config = [
            {
                "id": result["league_info"]["id"],
                "name": result["league_info"]["name"],
                "country": result["league_info"]["country"],
                "teams_count": result["teams_count"],
                "recent_matches": result["recent_matches_count"]
            }
            for result in accessible_leagues
        ]

        config_file = Path("data") / "accessible_leagues.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(accessible_config, f, ensure_ascii=False, indent=2)

        print(f"\n💾 可访问联赛配置已保存: {config_file}")

        return accessible_leagues

    return []


if __name__ == "__main__":
    asyncio.run(main())
