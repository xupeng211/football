#!/usr/bin/env python3
"""
诊断Football-Data.org API访问问题
"""

import asyncio
from datetime import datetime, timedelta

import aiohttp


async def test_basic_api_access():
    """测试基本API访问"""

    base_url = "https://api.football-data.org/v4"

    # 测试不同的请求方式
    test_cases = [
        {
            "name": "无认证 - 获取联赛列表",
            "url": f"{base_url}/competitions",
            "headers": {"Accept": "application/json"},
        },
        {
            "name": "无认证 - 获取世界杯数据",
            "url": f"{base_url}/competitions/2000",
            "headers": {"Accept": "application/json"},
        },
        {
            "name": "无认证 - 获取欧洲杯数据",
            "url": f"{base_url}/competitions/2018",
            "headers": {"Accept": "application/json"},
        },
        {
            "name": "无认证 - 获取荷甲数据",
            "url": f"{base_url}/competitions/2003",
            "headers": {"Accept": "application/json"},
        },
        {
            "name": "无认证 - 获取葡超数据",
            "url": f"{base_url}/competitions/2017",
            "headers": {"Accept": "application/json"},
        },
    ]

    print("🔍 诊断API访问问题...")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        for test_case in test_cases:
            print(f"\n📡 测试: {test_case['name']}")
            print(f"🌐 URL: {test_case['url']}")

            try:
                async with session.get(
                    test_case["url"], headers=test_case["headers"]
                ) as response:
                    print(f"📊 状态码: {response.status}")

                    if response.status == 200:
                        data = await response.json()

                        if "competitions" in data:
                            print(f"✅ 成功获取 {len(data['competitions'])} 个联赛")
                        elif "teams" in data:
                            print(f"✅ 成功获取 {len(data['teams'])} 支球队")
                        elif "matches" in data:
                            print(f"✅ 成功获取 {len(data['matches'])} 场比赛")
                        elif "name" in data:
                            print(f"✅ 联赛信息: {data.get('name')}")
                        else:
                            print("✅ 获取数据成功")

                    else:
                        error_text = await response.text()
                        print(f"❌ 请求失败: {error_text[:200]}")

                        # 检查是否是需要API密钥的错误
                        if (
                            "subscription" in error_text.lower()
                            or "permission" in error_text.lower()
                        ):
                            print("💡 提示: 可能需要注册API密钥")

            except Exception as e:
                print(f"❌ 网络错误: {e}")

            # 速率限制
            await asyncio.sleep(6)


async def test_date_range_limits():
    """测试日期范围限制"""

    base_url = "https://api.football-data.org/v4"
    headers = {"Accept": "application/json"}

    # 使用荷甲(免费版包含)测试不同日期范围
    competition_id = 2003  # 荷甲

    print(f"\n🗓️ 测试日期范围限制 - 荷甲 (ID: {competition_id})")
    print("-" * 40)

    # 测试不同时间范围
    date_ranges = [
        {"name": "最近7天", "days": 7},
        {"name": "最近30天", "days": 30},
        {"name": "最近90天", "days": 90},
        {"name": "最近180天", "days": 180},
        {"name": "最近365天", "days": 365},
    ]

    async with aiohttp.ClientSession() as session:
        for range_test in date_ranges:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=range_test["days"])

            params = {
                "dateFrom": start_date.strftime("%Y-%m-%d"),
                "dateTo": end_date.strftime("%Y-%m-%d"),
            }

            url = f"{base_url}/competitions/{competition_id}/matches"

            print(
                f"\n📅 测试 {range_test['name']} ({params['dateFrom']} 到 {params['dateTo']})"
            )

            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        matches = data.get("matches", [])
                        print(f"✅ 成功获取 {len(matches)} 场比赛")
                    else:
                        error_text = await response.text()
                        print(f"❌ 失败 ({response.status}): {error_text[:100]}")

            except Exception as e:
                print(f"❌ 错误: {e}")

            await asyncio.sleep(6)  # 速率限制


async def main():
    """主函数"""

    print("🔧 Football-Data.org API 访问诊断工具")
    print("=" * 60)

    # 基本访问测试
    await test_basic_api_access()

    # 日期范围测试
    await test_date_range_limits()

    print("\n" + "=" * 60)
    print("💡 诊断建议:")
    print("1. 如果所有请求都返回403,需要注册获取免费API密钥")
    print("2. 访问 https://www.football-data.org/client/register 注册")
    print("3. 免费版通常只能访问有限的联赛和时间范围")
    print("4. 查看 https://www.football-data.org/coverage 了解免费版覆盖范围")


if __name__ == "__main__":
    asyncio.run(main())
