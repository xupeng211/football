#!/usr/bin/env python3
"""
Football-Data.org API 密钥配置和测试脚本
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import aiohttp


def setup_env_file():
    """设置环境变量文件"""

    print("🔧 配置API密钥")
    print("=" * 50)

    # 读取.env模板
    env_template_path = Path(".env.template")
    env_path = Path(".env")

    if not env_template_path.exists():
        print("❌ 未找到 .env.template 文件")
        return False

    # 检查是否已有.env文件
    if env_path.exists():
        print("⚠️ .env 文件已存在")
        response = input("是否覆盖现有配置? (y/N): ").strip().lower()
        if response != "y":
            print("❌ 取消配置")
            return False

    # 获取API密钥
    print("\n🔑 请输入您的 Football-Data.org API 密钥:")
    print("(如果还没有,请访问: https://www.football-data.org/client/register)")
    api_key = input("API密钥: ").strip()

    if not api_key:
        print("❌ API密钥不能为空")
        return False

    # 读取模板并替换
    try:
        with open(env_template_path) as f:
            template_content = f.read()

        # 替换API密钥
        content = template_content.replace(
            "FOOTBALL_DATA_API_KEY=your_api_key_here",
            f"FOOTBALL_DATA_API_KEY={api_key}",
        )

        # 写入.env文件
        with open(env_path, "w") as f:
            f.write(content)

        print(f"✅ API密钥已配置到 {env_path}")
        return True

    except Exception as e:
        print(f"❌ 配置失败: {e}")
        return False


async def test_api_connection(api_key: str):
    """测试API连接"""

    print("\n🧪 测试API连接")
    print("=" * 50)

    base_url = "https://api.football-data.org/v4"
    headers = {"Accept": "application/json", "X-Auth-Token": api_key}

    # 测试用例 - 从免费版可访问的开始测试
    test_cases = [
        {
            "name": "获取联赛列表",
            "url": f"{base_url}/competitions",
            "expected_field": "competitions",
        },
        {
            "name": "测试世界杯数据",
            "url": f"{base_url}/competitions/2000",
            "expected_field": "name",
        },
        {
            "name": "测试英超比赛 (最近7天)",
            "url": f"{base_url}/competitions/2021/matches",
            "params": {
                "dateFrom": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "dateTo": datetime.now().strftime("%Y-%m-%d"),
            },
            "expected_field": "matches",
        },
    ]

    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. {test['name']}")

            try:
                params = test.get("params", {})
                async with session.get(
                    test["url"], headers=headers, params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        if test["expected_field"] in data:
                            if test["expected_field"] == "competitions":
                                count = len(data["competitions"])
                                print(f"   ✅ 成功! 获取到 {count} 个联赛")

                                # 显示免费版可用的联赛
                                print("   📋 免费版可用联赛:")
                                target_leagues = [
                                    "Premier League",
                                    "Championship",
                                    "Primera Division",
                                    "Bundesliga",
                                    "Serie A",
                                    "Ligue 1",
                                ]

                                for comp in data["competitions"]:
                                    if comp.get("name") in target_leagues:
                                        print(
                                            f"      • {comp['name']} (ID: {comp['id']})"
                                        )

                            elif test["expected_field"] == "matches":
                                count = len(data["matches"])
                                print(f"   ✅ 成功! 获取到 {count} 场比赛")
                            else:
                                print(f"   ✅ 成功! 获取到: {data.get('name', '数据')}")
                        else:
                            print("   ✅ 连接成功,但数据格式异常")

                    elif response.status == 403:
                        error_text = await response.text()
                        print("   ❌ 权限被拒 (403)")
                        if "subscription" in error_text.lower():
                            print("   💡 提示: 该联赛需要付费订阅")
                        else:
                            print("   💡 提示: 检查API密钥是否正确")

                    elif response.status == 429:
                        print("   ⏳ 请求过于频繁 (429) - 免费版每分钟最多10次")

                    else:
                        error_text = await response.text()
                        print(f"   ❌ 请求失败 ({response.status}): {error_text[:100]}")

            except Exception as e:
                print(f"   ❌ 网络错误: {e}")

            # 遵守速率限制
            if i < len(test_cases):
                print("   ⏱️ 等待6秒避免速率限制...")
                await asyncio.sleep(6)


def print_next_steps():
    """打印后续步骤指南"""

    print("\n📋 后续步骤指南")
    print("=" * 50)
    print("""
🎯 数据抓取计划:

1️⃣ 注册API密钥:
   • 访问: https://www.football-data.org/client/register
   • 选择免费计划 (Free Tier)
   • 验证邮箱获取API密钥

2️⃣ 抓取优先级:
   🥇 Priority 1 (每天更新):
      • 英超 (ID: 2021) - 最受关注
      • 英冠 (ID: 2016) - 您特别要求

   🥈 Priority 2 (每2天更新):
      • 西甲 (ID: 2014)
      • 德甲 (ID: 2002)
      • 意甲 (ID: 2019)
      • 法甲 (ID: 2015)

3️⃣ 数据抓取策略:
   • 免费版限制: 最近6个月数据 ✅
   • 速率限制: 每分钟10次请求
   • 建议批次: 每次抓取7天数据
   • 总时间: 约需要3-4小时完成所有联赛

4️⃣ 存储容量估算:
   🏆 6个联赛 x 6个月 ≈ 1,800场比赛
   📊 每场比赛数据 ≈ 2KB (基础数据 + 赔率)
   💾 总容量需求 ≈ 3.6MB + 索引 ≈ 10MB

   对于SQLite数据库: 50MB已绰绰有余! 🎉

5️⃣ 分析能力:
   ✅ 已验证: 我们的系统可以分析联赛模式、赔率准确性
   ✅ 可扩展: 支持机器学习预测模型
   ✅ 可视化: 支持图表生成和报告输出
""")


def main():
    """主函数"""

    print("🚀 Football-Data.org API 配置助手")
    print("=" * 60)

    # 检查当前环境
    current_key = os.getenv("FOOTBALL_DATA_API_KEY")

    if current_key:
        print(f"✅ 检测到现有API密钥: {current_key[:8]}...***")
        print("正在测试连接...")

        # 测试现有密钥
        asyncio.run(test_api_connection(current_key))

    else:
        print("❌ 未检测到API密钥")

        # 询问是否要配置
        response = input("\n是否现在配置API密钥? (y/N): ").strip().lower()

        if response == "y":
            if setup_env_file():
                # 重新读取密钥并测试
                from dotenv import load_dotenv

                load_dotenv()
                new_key = os.getenv("FOOTBALL_DATA_API_KEY")

                if new_key:
                    asyncio.run(test_api_connection(new_key))
        else:
            print("⏭️ 跳过API配置")

    # 显示后续步骤
    print_next_steps()


if __name__ == "__main__":
    main()
