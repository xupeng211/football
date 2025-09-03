#!/usr/bin/env python3
"""
足球数据分析演示 - 简化版 (无需外部绘图库)
"""

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pandas as pd
except ImportError:
    print("❌ pandas未安装,使用基础Python进行分析...")
    pd = None


class SimpleFootballAnalyzer:
    """简化的足球数据分析器"""

    def __init__(self):
        self.data_dir = Path("data")

    def create_demo_matches(self):
        """创建演示比赛数据"""
        print("🏗️ 创建演示比赛数据...")

        leagues = {
            "英超": {"teams": 20, "style": "high_scoring"},
            "西甲": {"teams": 20, "style": "technical"},
            "德甲": {"teams": 18, "style": "attacking"},
            "意甲": {"teams": 20, "style": "defensive"},
            "法甲": {"teams": 20, "style": "balanced"},
            "英冠": {"teams": 24, "style": "competitive"},
        }

        matches = []
        match_id = 1

        for league_name, league_info in leagues.items():
            print(f"  📊 生成{league_name}数据...")

            # 每个联赛最近30天的比赛
            for day in range(30):
                match_date = datetime.now() - timedelta(days=day)

                # 根据联赛风格调整数据
                if league_info["style"] == "high_scoring":
                    avg_goals = 2.8
                elif league_info["style"] == "defensive":
                    avg_goals = 2.2
                else:
                    avg_goals = 2.5

                # 每天1-2场比赛
                daily_matches = random.randint(1, 2)

                for _i in range(daily_matches):
                    # 生成符合联赛特点的比分
                    total_goals = max(0, int(random.normalvariate(avg_goals, 1.2)))
                    home_score = random.randint(0, total_goals)
                    away_score = total_goals - home_score

                    # 确定结果
                    if home_score > away_score:
                        result = "H"
                    elif home_score < away_score:
                        result = "A"
                    else:
                        result = "D"

                    # 生成赔率(基于结果的反向计算)
                    if result == "H":
                        home_odds = round(random.uniform(1.4, 2.5), 2)
                        away_odds = round(random.uniform(2.5, 5.0), 2)
                    elif result == "A":
                        home_odds = round(random.uniform(2.5, 5.0), 2)
                        away_odds = round(random.uniform(1.4, 2.5), 2)
                    else:
                        home_odds = round(random.uniform(2.0, 4.0), 2)
                        away_odds = round(random.uniform(2.0, 4.0), 2)

                    draw_odds = round(random.uniform(2.8, 4.2), 2)

                    match = {
                        "match_id": match_id,
                        "league": league_name,
                        "date": match_date.strftime("%Y-%m-%d"),
                        "home_team": f"{league_name[:2]}主队{random.randint(1, league_info['teams'])}",
                        "away_team": f"{league_name[:2]}客队{random.randint(1, league_info['teams'])}",
                        "home_score": home_score,
                        "away_score": away_score,
                        "total_goals": total_goals,
                        "result": result,
                        "home_odds": home_odds,
                        "draw_odds": draw_odds,
                        "away_odds": away_odds,
                    }
                    matches.append(match)
                    match_id += 1

        print(f"✅ 生成了 {len(matches)} 场比赛数据")
        return matches

    def analyze_basic_stats(self, matches):
        """基础统计分析"""
        print("\n📊 基础统计分析")
        print("=" * 60)

        # 总体统计
        total_matches = len(matches)
        total_goals = sum(m["total_goals"] for m in matches)

        print("📈 总体数据:")
        print(f"  • 总比赛数: {total_matches}")
        print(f"  • 总进球数: {total_goals}")
        print(f"  • 场均进球: {total_goals / total_matches:.2f}")

        # 按联赛统计
        print("\n🏆 各联赛统计:")
        leagues = {}

        for match in matches:
            league = match["league"]
            if league not in leagues:
                leagues[league] = {
                    "matches": 0,
                    "goals": 0,
                    "home_wins": 0,
                    "draws": 0,
                    "away_wins": 0,
                }

            leagues[league]["matches"] += 1
            leagues[league]["goals"] += match["total_goals"]

            if match["result"] == "H":
                leagues[league]["home_wins"] += 1
            elif match["result"] == "D":
                leagues[league]["draws"] += 1
            else:
                leagues[league]["away_wins"] += 1

        for league, stats in leagues.items():
            matches_count = stats["matches"]
            avg_goals = stats["goals"] / matches_count
            home_win_rate = stats["home_wins"] / matches_count * 100

            print(f"  • {league}:")
            print(f"    📊 {matches_count} 场比赛, 场均{avg_goals:.2f}球")
            print(f"    🏠 主场胜率: {home_win_rate:.1f}%")

        return leagues

    def analyze_odds_accuracy(self, matches):
        """分析赔率准确性"""
        print("\n💰 赔率准确性分析")
        print("=" * 60)

        correct_predictions = 0
        total_predictions = 0

        for match in matches:
            # 找出最低赔率对应的预测结果
            odds = {
                "H": match["home_odds"],
                "D": match["draw_odds"],
                "A": match["away_odds"],
            }

            predicted = min(odds, key=odds.get)  # 最低赔率
            actual = match["result"]

            if predicted == actual:
                correct_predictions += 1
            total_predictions += 1

        accuracy = correct_predictions / total_predictions
        print(
            f"🎯 赔率预测准确率: {accuracy:.1%} ({correct_predictions}/{total_predictions})"
        )

        # 按联赛分析准确率
        league_accuracy = {}
        for match in matches:
            league = match["league"]
            if league not in league_accuracy:
                league_accuracy[league] = {"correct": 0, "total": 0}

            odds = {
                "H": match["home_odds"],
                "D": match["draw_odds"],
                "A": match["away_odds"],
            }
            predicted = min(odds, key=odds.get)

            league_accuracy[league]["total"] += 1
            if predicted == match["result"]:
                league_accuracy[league]["correct"] += 1

        print("\n📊 各联赛预测准确率:")
        for league, stats in league_accuracy.items():
            rate = stats["correct"] / stats["total"]
            print(f"  • {league}: {rate:.1%}")

        return accuracy

    def save_analysis_results(self, matches, leagues_stats, accuracy):
        """保存分析结果"""
        print("\n💾 保存分析结果...")

        # 创建分析结果目录
        results_dir = Path("data/analysis_results")
        results_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存原始数据
        matches_file = results_dir / f"demo_matches_{timestamp}.json"
        with open(matches_file, "w", encoding="utf-8") as f:
            json.dump(matches, f, ensure_ascii=False, indent=2)
        print(f"📁 比赛数据: {matches_file}")

        # 保存分析报告
        report = {
            "分析时间": datetime.now().isoformat(),
            "数据类型": "演示数据",
            "分析结果": {
                "总比赛数": len(matches),
                "联赛数量": len(leagues_stats),
                "平均场均进球": sum(
                    s["goals"] / s["matches"] for s in leagues_stats.values()
                )
                / len(leagues_stats),
                "整体主场胜率": sum(
                    s["home_wins"] / s["matches"] for s in leagues_stats.values()
                )
                / len(leagues_stats),
                "赔率预测准确率": accuracy,
            },
            "联赛详情": {
                name: {
                    "比赛场次": stats["matches"],
                    "场均进球": round(stats["goals"] / stats["matches"], 2),
                    "主场胜率": round(stats["home_wins"] / stats["matches"], 3),
                    "平局率": round(stats["draws"] / stats["matches"], 3),
                    "客场胜率": round(stats["away_wins"] / stats["matches"], 3),
                }
                for name, stats in leagues_stats.items()
            },
        }

        report_file = results_dir / f"analysis_report_{timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📋 分析报告: {report_file}")

        return report_file


def main():
    """主函数"""

    print("⚽ 足球数据分析系统演示")
    print("=" * 60)

    analyzer = SimpleFootballAnalyzer()

    # 创建演示数据
    matches = analyzer.create_demo_matches()

    # 执行分析
    leagues_stats = analyzer.analyze_basic_stats(matches)
    accuracy = analyzer.analyze_odds_accuracy(matches)

    # 保存结果
    report_file = analyzer.save_analysis_results(matches, leagues_stats, accuracy)

    print("\n" + "🎉 分析演示完成!".center(60, "="))

    # API注册指南
    print("\n🔑 获取真实数据的步骤:")
    print("1. 访问: https://www.football-data.org/client/register")
    print("2. 注册免费账户 (无需信用卡)")
    print("3. 获取API密钥")
    print("4. 免费版限制: 12个联赛, 最近6个月数据, 每分钟10次请求")
    print("5. 包含五大联赛和英冠! ✅")

    print("\n💡 有了API密钥后,我们可以:")
    print("  • 抓取真实的比赛数据和赔率")
    print("  • 训练机器学习预测模型")
    print("  • 实时分析和预测")
    print("  • 建立完整的数据仓库")

    print(f"\n📊 演示结果已保存到: {report_file}")


if __name__ == "__main__":
    main()
