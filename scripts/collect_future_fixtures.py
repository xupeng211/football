#!/usr/bin/env python3
"""
专门抓取未来赛程的脚本
"""

import asyncio
import os
import sqlite3
from datetime import datetime, timedelta

import aiohttp

# 目标联赛
TARGET_LEAGUES = {
    "英超": {"id": 2021, "name": "Premier League"},
    "英冠": {"id": 2016, "name": "Championship"},
    "西甲": {"id": 2014, "name": "Primera Division"},
    "德甲": {"id": 2002, "name": "Bundesliga"},
    "意甲": {"id": 2019, "name": "Serie A"},
    "法甲": {"id": 2015, "name": "Ligue 1"},
}


def _get_api_config():
    """获取API配置"""
    api_key = os.getenv("FOOTBALL_DATA_API_KEY")
    if not api_key:
        return None, None, None

    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    params = {
        "dateFrom": start_date.strftime("%Y-%m-%d"),
        "dateTo": end_date.strftime("%Y-%m-%d"),
    }

    headers = {"Accept": "application/json", "X-Auth-Token": api_key}
    return headers, params, (start_date, end_date)


def _filter_future_matches(matches):
    """筛选未来比赛"""
    future_matches = []
    for match in matches:
        if match.get("status") in ["SCHEDULED", "TIMED", "POSTPONED"]:
            future_matches.append(match)
    return future_matches


def _save_matches_to_db(cursor, matches, league_id, league_name):
    """保存比赛到数据库"""
    saved_count = 0
    for match in matches:
        try:
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
                    None,
                    None,
                    None,
                ),
            )
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"    ⚠️ 保存错误: {e}")
    return saved_count


def _display_sample_matches(matches):
    """显示示例比赛"""
    if not matches:
        return

    print("  📋 即将到来的比赛:")
    for i, match in enumerate(matches[:3]):
        date_str = match.get("utcDate", "")[:10] if match.get("utcDate") else "未定"
        home = match.get("homeTeam", {}).get("name", "未知")
        away = match.get("awayTeam", {}).get("name", "未知")
        print(f"    {i + 1}. {date_str} | {home} vs {away}")


async def _process_league(
    session, base_url, headers, params, league_name, league_id, cursor
):
    """处理单个联赛的数据获取"""
    print(f"\n🏆 {league_name} (ID: {league_id})")
    print("-" * 30)

    try:
        url = f"{base_url}/competitions/{league_id}/matches"
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                matches = data.get("matches", [])
                future_matches = _filter_future_matches(matches)

                print(f"  📈 找到 {len(future_matches)} 场未来比赛")

                saved_count = _save_matches_to_db(
                    cursor, future_matches, league_id, league_name
                )
                print(f"  💾 保存了 {saved_count} 场新的未来比赛")

                _display_sample_matches(future_matches)
                return saved_count

            elif response.status == 403:
                print("  ❌ 权限不足,可能需要付费版")
            else:
                error_text = await response.text()
                print(f"  ❌ 请求失败 ({response.status}): {error_text[:100]}")

    except Exception as e:
        print(f"  ❌ 网络错误: {e}")

    return 0


async def collect_future_fixtures():
    """抓取未来赛程"""
    headers, params, date_range = _get_api_config()
    if not headers:
        print("❌ API密钥未配置")
        return

    print("📅 抓取未来赛程")
    print("=" * 60)
    print(f"🗓️ 查询时间范围: {params['dateFrom']} 到 {params['dateTo']}")

    base_url = "https://api.football-data.org/v4"
    conn = sqlite3.connect("football_data.db")
    cursor = conn.cursor()

    async with aiohttp.ClientSession() as session:
        total_future_matches = 0

        for league_name, league_info in TARGET_LEAGUES.items():
            league_id = league_info["id"]
            saved_count = await _process_league(
                session, base_url, headers, params, league_name, league_id, cursor
            )
            total_future_matches += saved_count
            await asyncio.sleep(6)  # 避免速率限制

    conn.commit()
    conn.close()

    print("\n🎯 未来赛程抓取总结:")
    print(f"  • 新增未来比赛: {total_future_matches} 场")

    return total_future_matches


if __name__ == "__main__":
    asyncio.run(collect_future_fixtures())
