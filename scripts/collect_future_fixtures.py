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
    "法甲": {"id": 2015, "name": "Ligue 1"}
}


async def collect_future_fixtures():
    """抓取未来赛程"""

    api_key = os.getenv("FOOTBALL_DATA_API_KEY")
    if not api_key:
        print("❌ API密钥未配置")
        return

    print("📅 抓取未来赛程")
    print("=" * 60)

    base_url = "https://api.football-data.org/v4"
    headers = {
        "Accept": "application/json",
        "X-Auth-Token": api_key
    }

    # 设置未来时间范围 (接下来30天)
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)

    params = {
        "dateFrom": start_date.strftime("%Y-%m-%d"),
        "dateTo": end_date.strftime("%Y-%m-%d")
    }

    print(f"🗓️ 查询时间范围: {params['dateFrom']} 到 {params['dateTo']}")

    # 连接数据库
    conn = sqlite3.connect("football_data.db")
    cursor = conn.cursor()

    async with aiohttp.ClientSession() as session:
        total_future_matches = 0

        for league_name, league_info in TARGET_LEAGUES.items():
            league_id = league_info["id"]

            print(f"\n🏆 {league_name} (ID: {league_id})")
            print("-" * 30)

            try:
                url = f"{base_url}/competitions/{league_id}/matches"

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches = data.get("matches", [])

                        # 筛选真正的未来比赛
                        future_matches = []
                        for match in matches:
                            if match.get("status") in ["SCHEDULED", "TIMED", "POSTPONED"]:
                                future_matches.append(match)

                        print(f"  📈 找到 {len(future_matches)} 场未来比赛")

                        # 保存到数据库
                        saved_count = 0
                        for match in future_matches:
                            try:
                                cursor.execute('''
                                    INSERT OR IGNORE INTO real_matches
                                    (api_id, league_id, league_name, season, matchday, status, 
                                     utc_date, home_team_id, home_team_name, away_team_id, 
                                     away_team_name, home_score, away_score, result)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    match.get('id'),
                                    league_id,
                                    league_name,
                                    match.get('season', {}).get('id'),
                                    match.get('matchday'),
                                    match.get('status'),
                                    match.get('utcDate'),
                                    match.get('homeTeam', {}).get('id'),
                                    match.get('homeTeam', {}).get('name'),
                                    match.get('awayTeam', {}).get('id'),
                                    match.get('awayTeam', {}).get('name'),
                                    None,  # home_score
                                    None,  # away_score
                                    None   # result
                                ))

                                if cursor.rowcount > 0:
                                    saved_count += 1

                            except Exception as e:
                                print(f'    ⚠️ 保存错误: {e}')

                        print(f'  💾 保存了 {saved_count} 场新的未来比赛')
                        total_future_matches += saved_count

                        # 显示一些示例
                        if future_matches:
                            print('  📋 即将到来的比赛:')
                            for i, match in enumerate(future_matches[:3]):
                                date_str = match.get('utcDate', '')[:10] if match.get('utcDate') else '未定'
                                home = match.get('homeTeam', {}).get('name', '未知')
                                away = match.get('awayTeam', {}).get('name', '未知')
                                print(f'    {i+1}. {date_str} | {home} vs {away}')

                    elif response.status == 403:
                        print('  ❌ 权限不足，可能需要付费版')
                    else:
                        error_text = await response.text()
                        print(f'  ❌ 请求失败 ({response.status}): {error_text[:100]}')

            except Exception as e:
                print(f'  ❌ 网络错误: {e}')

            # 避免速率限制
            await asyncio.sleep(6)

    conn.commit()
    conn.close()

    print('\n🎯 未来赛程抓取总结:')
    print(f'  • 新增未来比赛: {total_future_matches} 场')

    return total_future_matches


if __name__ == '__main__':
    asyncio.run(collect_future_fixtures())
