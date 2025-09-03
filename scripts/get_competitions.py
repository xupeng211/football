#!/usr/bin/env python3
"""
获取Football-Data.org所有可用联赛的脚本
"""

import asyncio
import sys
from pathlib import Path

import aiohttp
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def get_all_competitions():
    """获取所有可用的联赛"""

    # 免费API的基本URL
    base_url = "https://api.football-data.org/v4"

    headers = {
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            # 获取所有联赛
            url = f"{base_url}/competitions"
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    competitions = data.get("competitions", [])

                    print(f"🏆 找到 {len(competitions)} 个联赛:")
                    print("-" * 80)

                    # 创建DataFrame便于查看
                    df_data = []
                    for comp in competitions:
                        df_data.append({
                            "ID": comp.get("id"),
                            "名称": comp.get("name"),
                            "代码": comp.get("code"),
                            "国家": comp.get("area", {}).get("name", ""),
                            "类型": comp.get("type", ""),
                            "计划": comp.get("plan", "")
                        })

                    df = pd.DataFrame(df_data)

                    # 显示所有联赛
                    print(df.to_string(index=False))

                    # 特别标记五大联赛和英冠
                    print("\n" + "=" * 80)
                    print("🎯 目标联赛:")

                    target_leagues = {
                        "Premier League": "英超",
                        "La Liga": "西甲",
                        "Bundesliga": "德甲",
                        "Serie A": "意甲",
                        "Ligue 1": "法甲",
                        "Championship": "英冠",
                        "EFL Championship": "英冠"
                    }

                    for comp in competitions:
                        name = comp.get("name", "")
                        for target_name, chinese_name in target_leagues.items():
                            if target_name.lower() in name.lower():
                                area_name = comp.get('area', {}).get('name', '')
                                comp_id = comp.get('id')
                                print(f"✅ {chinese_name}: ID={comp_id} | {name} | {area_name}")

                    return competitions

                else:
                    print(f"❌ API请求失败: {response.status}")
                    print(f"响应: {await response.text()}")
                    return []

        except Exception as e:
            print(f"❌ 网络错误: {e}")
            return []


if __name__ == "__main__":
    print("🔍 正在获取Football-Data.org API的所有联赛...")
    competitions = asyncio.run(get_all_competitions())

    if competitions:
        print(f"\n✅ 成功获取 {len(competitions)} 个联赛信息!")
    else:
        print("\n❌ 获取联赛信息失败")
