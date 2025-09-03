#!/usr/bin/env python3
"""
快速API测试 - 验证密钥配置
"""

import asyncio
import os
from pathlib import Path

import aiohttp


async def test_api_key(api_key: str):
    """测试API密钥是否有效"""

    print(f"🔑 测试API密钥: {api_key[:8]}...***")

    base_url = "https://api.football-data.org/v4"
    headers = {
        "Accept": "application/json",
        "X-Auth-Token": api_key
    }

    async with aiohttp.ClientSession() as session:
        # 测试基本连接
        try:
            async with session.get(f"{base_url}/competitions", headers=headers) as response:
                print(f"📡 请求状态: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    competitions = data.get("competitions", [])
                    print(f"✅ API密钥有效! 获取到 {len(competitions)} 个联赛")

                    # 显示目标联赛是否可用
                    target_leagues = {
                        "Premier League": 2021,
                        "Championship": 2016,
                        "Primera Division": 2014,
                        "Bundesliga": 2002,
                        "Serie A": 2019,
                        "Ligue 1": 2015
                    }

                    print("\n🎯 检查目标联赛可用性:")
                    available_leagues = []

                    for comp in competitions:
                        comp_name = comp.get("name", "")
                        comp_id = comp.get("id")

                        for target_name, target_id in target_leagues.items():
                            if target_name in comp_name or comp_id == target_id:
                                print(f"  ✅ {comp_name} (ID: {comp_id})")
                                available_leagues.append(comp_id)
                                break

                    return True, available_leagues

                elif response.status == 401:
                    print("❌ API密钥无效或已过期")
                    error_text = await response.text()
                    print(f"错误详情: {error_text}")
                    return False, []

                elif response.status == 403:
                    print("❌ 权限不足 - 可能需要验证邮箱或升级账户")
                    error_text = await response.text()
                    print(f"错误详情: {error_text}")
                    return False, []

                else:
                    error_text = await response.text()
                    print(f"❌ 请求失败 ({response.status}): {error_text}")
                    return False, []

        except Exception as e:
            print(f"❌ 网络连接错误: {e}")
            return False, []


def get_api_key_from_user():
    """从用户获取API密钥"""

    print("\n🔑 请提供您的 Football-Data.org API 密钥:")
    print("格式应该类似: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6")

    api_key = input("API密钥: ").strip()

    if len(api_key) < 20:
        print("⚠️ API密钥长度似乎不正确，通常应该是32个字符")
        confirm = input("确定要使用这个密钥吗? (y/N): ").strip().lower()
        if confirm != 'y':
            return None

    return api_key


def update_env_file(api_key: str):
    """更新.env文件中的API密钥"""

    env_path = Path(".env")

    try:
        # 读取现有内容
        with open(env_path) as f:
            content = f.read()

        # 替换API密钥
        updated_content = content.replace(
            "FOOTBALL_DATA_API_KEY=your_football_data_api_key_here",
            f"FOOTBALL_DATA_API_KEY={api_key}"
        )

        # 如果没有找到占位符，尝试其他可能的格式
        if updated_content == content:
            import re
            updated_content = re.sub(
                r'FOOTBALL_DATA_API_KEY=.*',
                f'FOOTBALL_DATA_API_KEY={api_key}',
                content
            )

        # 写回文件
        with open(env_path, 'w') as f:
            f.write(updated_content)

        print(f"✅ API密钥已更新到 {env_path}")
        return True

    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False


async def main():
    """主函数"""

    print("🚀 API密钥配置诊断工具")
    print("=" * 60)

    # 检查当前配置
    current_key = os.getenv("FOOTBALL_DATA_API_KEY")

    if current_key and current_key != "your_football_data_api_key_here":
        print("📋 检测到配置的API密钥")

        # 测试现有密钥
        success, available_leagues = await test_api_key(current_key)

        if success:
            print("\n🎉 API密钥验证成功! 可以开始抓取数据了")
            print(f"📊 可用联赛数量: {len(available_leagues)}")
            return True
        else:
            print("\n❌ 当前API密钥无效")
    else:
        print("❌ 未检测到有效的API密钥配置")

    # 需要重新配置
    print("\n🔧 让我们重新配置API密钥...")

    api_key = get_api_key_from_user()
    if not api_key:
        print("❌ 取消配置")
        return False

    # 测试新密钥
    print("\n🧪 测试新API密钥...")
    success, available_leagues = await test_api_key(api_key)

    if success:
        # 更新配置文件
        if update_env_file(api_key):
            print("\n🎉 配置完成! 现在可以开始抓取数据了")
            return True
    else:
        print("\n❌ 提供的API密钥无效，请检查后重试")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())

    if success:
        print("\n📋 下一步:")
        print("运行: python scripts/collect_real_data.py")
    else:
        print("\n💡 获取API密钥:")
        print("1. 访问: https://www.football-data.org/client/register")
        print("2. 注册并验证邮箱")
        print("3. 在控制台获取API密钥")
        print("4. 重新运行此脚本配置密钥")
