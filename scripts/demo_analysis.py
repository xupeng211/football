#!/usr/bin/env python3
"""
足球数据分析演示 - 使用样本数据展示分析能力
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 支持中文
plt.rcParams['axes.unicode_minus'] = False


class FootballDataAnalyzer:
    """足球数据分析器演示版"""

    def __init__(self):
        self.data_dir = Path("data")

    def load_sample_data(self):
        """加载样本数据"""
        print("📁 加载样本数据...")

        # 读取赔率样本数据
        odds_file = self.data_dir / "samples" / "odds_sample.json"
        with open(odds_file, encoding='utf-8') as f:
            odds_data = json.load(f)

        odds_df = pd.DataFrame(odds_data)
        print(f"✅ 赔率数据: {len(odds_df)} 条记录")

        return {"odds": odds_df}

    def create_synthetic_match_data(self):
        """创建合成的比赛数据用于演示"""
        print("🏗️ 创建演示用的比赛数据...")

        # 模拟五大联赛的比赛数据
        leagues = ["英超", "西甲", "德甲", "意甲", "法甲", "英冠"]
        teams_per_league = {"英超": 20, "西甲": 20, "德甲": 18, "意甲": 20, "法甲": 20, "英冠": 24}

        matches = []
        match_id = 1

        for league in leagues:
            # 每个联赛模拟最近30天的比赛
            for day in range(30):
                match_date = datetime.now() - timedelta(days=day)

                # 每天1-3场比赛
                daily_matches = min(3, teams_per_league[league] // 10)

                for i in range(daily_matches):
                    # 随机生成比分
                    import random
                    home_score = random.randint(0, 4)
                    away_score = random.randint(0, 4)

                    # 根据比分确定结果
                    if home_score > away_score:
                        result = "H"  # 主队胜
                    elif home_score < away_score:
                        result = "A"  # 客队胜
                    else:
                        result = "D"  # 平局

                    match = {
                        "match_id": match_id,
                        "league": league,
                        "date": match_date.strftime("%Y-%m-%d"),
                        "home_team": f"主队{random.randint(1, teams_per_league[league])}",
                        "away_team": f"客队{random.randint(1, teams_per_league[league])}",
                        "home_score": home_score,
                        "away_score": away_score,
                        "result": result,
                        "home_odds": round(random.uniform(1.5, 4.0), 2),
                        "draw_odds": round(random.uniform(2.8, 4.5), 2),
                        "away_odds": round(random.uniform(1.5, 4.0), 2)
                    }
                    matches.append(match)
                    match_id += 1

        return pd.DataFrame(matches)

    def analyze_league_patterns(self, matches_df: pd.DataFrame):
        """分析联赛模式"""
        print("\n📊 联赛数据分析")
        print("=" * 60)

        # 按联赛统计
        league_stats = matches_df.groupby('league').agg({
            'match_id': 'count',
            'home_score': 'mean',
            'away_score': 'mean',
            'result': lambda x: (x == 'H').mean()  # 主场胜率
        }).round(2)

        league_stats.columns = ['比赛场次', '主队场均进球', '客队场均进球', '主场胜率']
        print("\n🏆 各联赛统计:")
        print(league_stats)

        # 进球分布分析
        print("\n⚽ 进球分布分析:")
        total_goals = matches_df['home_score'] + matches_df['away_score']
        print(f"  • 平均每场进球: {total_goals.mean():.2f}")
        print(f"  • 最高单场进球: {total_goals.max()}")
        print(f"  • 最低单场进球: {total_goals.min()}")

        # 结果分布
        result_dist = matches_df['result'].value_counts(normalize=True) * 100
        print("\n📈 比赛结果分布:")
        print(f"  • 主队胜: {result_dist.get('H', 0):.1f}%")
        print(f"  • 平局: {result_dist.get('D', 0):.1f}%")
        print(f"  • 客队胜: {result_dist.get('A', 0):.1f}%")

        return league_stats

    def analyze_odds_patterns(self, matches_df: pd.DataFrame):
        """分析赔率模式"""
        print("\n💰 赔率分析")
        print("=" * 60)

        # 赔率统计
        odds_stats = matches_df[['home_odds', 'draw_odds', 'away_odds']].describe()
        print("\n📊 赔率统计:")
        print(odds_stats.round(2))

        # 赔率与结果的关系
        print("\n🎯 赔率准确性分析:")

        # 找出最低赔率对应的预测
        matches_df['predicted_result'] = matches_df[['home_odds', 'draw_odds', 'away_odds']].apply(
            lambda row: 'H' if row['home_odds'] == row.min() else
                        ('D' if row['draw_odds'] == row.min() else 'A'), axis=1
        )

        # 计算预测准确率
        accuracy = (matches_df['predicted_result'] == matches_df['result']).mean()
        print(f"  • 最低赔率预测准确率: {accuracy:.1%}")

        return accuracy

    def create_visualizations(self, matches_df: pd.DataFrame, league_stats: pd.DataFrame):
        """创建可视化图表"""
        print("\n📈 生成数据可视化图表...")

        # 创建图表目录
        charts_dir = Path("data/analysis_charts")
        charts_dir.mkdir(exist_ok=True)

        # 1. 联赛比赛数量对比
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('足球数据分析演示', fontsize=16, fontweight='bold')

        # 比赛场次对比
        league_stats['比赛场次'].plot(kind='bar', ax=axes[0,0], color='skyblue')
        axes[0,0].set_title('各联赛比赛场次')
        axes[0,0].set_ylabel('场次')
        axes[0,0].tick_params(axis='x', rotation=45)

        # 主场胜率对比
        league_stats['主场胜率'].plot(kind='bar', ax=axes[0,1], color='lightgreen')
        axes[0,1].set_title('各联赛主场胜率')
        axes[0,1].set_ylabel('胜率')
        axes[0,1].tick_params(axis='x', rotation=45)

        # 进球分布
        total_goals = matches_df['home_score'] + matches_df['away_score']
        total_goals.hist(bins=10, ax=axes[1,0], color='orange', alpha=0.7)
        axes[1,0].set_title('单场比赛进球数分布')
        axes[1,0].set_xlabel('进球数')
        axes[1,0].set_ylabel('频次')

        # 结果分布饼图
        result_counts = matches_df['result'].value_counts()
        labels = ['主队胜', '平局', '客队胜']
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        axes[1,1].pie(result_counts.values, labels=labels, colors=colors, autopct='%1.1f%%')
        axes[1,1].set_title('比赛结果分布')

        plt.tight_layout()
        chart_file = charts_dir / "football_analysis_demo.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        print(f"📊 图表已保存: {chart_file}")

        return chart_file

    def generate_analysis_report(self, matches_df: pd.DataFrame, accuracy: float):
        """生成分析报告"""
        print("\n📝 生成分析报告...")

        report = {
            "分析时间": datetime.now().isoformat(),
            "数据概况": {
                "总比赛数": len(matches_df),
                "联赛数量": matches_df['league'].nunique(),
                "分析时间范围": "最近30天",
                "数据来源": "演示样本数据"
            },
            "关键发现": {
                "平均每场进球": float((matches_df['home_score'] + matches_df['away_score']).mean()),
                "主场优势": float(matches_df.groupby('result').size()['H'] / len(matches_df)),
                "赔率预测准确率": float(accuracy),
                "最活跃联赛": str(matches_df['league'].value_counts().index[0])
            },
            "联赛对比": {
                league: {
                    "比赛场次": int(group['match_id'].count()),
                    "场均进球": float((group['home_score'] + group['away_score']).mean()),
                    "主场胜率": float((group['result'] == 'H').mean())
                }
                for league, group in matches_df.groupby('league')
            },
            "下一步建议": [
                "注册 football-data.org 免费API密钥获取真实数据",
                "收集最近6个月的比赛数据",
                "建立机器学习预测模型",
                "实施实时数据更新机制",
                "添加更多数据源以提高准确性"
            ]
        }

        # 保存报告
        report_file = Path("data/analysis_charts/analysis_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📋 分析报告已保存: {report_file}")
        return report

    def run_demo_analysis(self):
        """运行完整的演示分析"""
        print("🎬 足球数据分析演示")
        print("=" * 60)

        # 加载和创建数据
        sample_data = self.load_sample_data()
        matches_df = self.create_synthetic_match_data()

        print("\n📊 分析数据概况:")
        print(f"  • 比赛数据: {len(matches_df)} 场比赛")
        print(f"  • 赔率数据: {len(sample_data['odds'])} 条记录")
        print(f"  • 覆盖联赛: {', '.join(matches_df['league'].unique())}")

        # 执行分析
        league_stats = self.analyze_league_patterns(matches_df)
        accuracy = self.analyze_odds_patterns(matches_df)

        # 生成可视化
        chart_file = self.create_visualizations(matches_df, league_stats)

        # 生成报告
        report = self.generate_analysis_report(matches_df, accuracy)

        return {
            "matches_data": matches_df,
            "league_stats": league_stats,
            "chart_file": chart_file,
            "report": report
        }


def print_api_registration_guide():
    """打印API注册指南"""
    print("\n" + "🔑 API注册指南".center(60, "="))
    print("""
📝 获取免费API密钥步骤:

1️⃣ 访问注册页面:
   https://www.football-data.org/client/register

2️⃣ 填写注册信息:
   • 邮箱地址
   • 用途说明 (选择: 个人学习项目)
   • 编程语言 (选择: Python)

3️⃣ 免费版权限:
   ✅ 12个联赛 (包括五大联赛!)
   ✅ 基础数据：赛程、结果、积分榜
   ✅ 每分钟10次请求
   ⚠️ 时间限制：通常只能获取最近6个月数据

4️⃣ 配置API密钥:
   export FOOTBALL_DATA_API_KEY="your_api_key_here"

5️⃣ 可抓取的联赛:
   • 英超 (ID: 2021) ⭐
   • 西甲 (ID: 2014) ⭐  
   • 德甲 (ID: 2002) ⭐
   • 意甲 (ID: 2019) ⭐
   • 法甲 (ID: 2015) ⭐
   • 英冠 (ID: 2016) ⭐
   • 欧冠 (ID: 2001)
   • 荷甲 (ID: 2003)
   • 葡超 (ID: 2017)
   • 巴甲 (ID: 2013)
""")


def main():
    """主函数"""

    # 运行分析演示
    analyzer = FootballDataAnalyzer()
    results = analyzer.run_demo_analysis()

    print("\n" + "🎉 演示分析完成!".center(60, "="))
    print(f"""
📈 分析结果摘要:
  • 处理了 {len(results['matches_data'])} 场比赛数据
  • 覆盖 6 个联赛
  • 生成了完整的可视化图表
  • 创建了详细的分析报告

📁 输出文件:
  • 图表: {results['chart_file']}
  • 报告: data/analysis_charts/analysis_report.json

🚀 这就是我们数据分析系统的能力演示！
   有了真实数据后，我们可以进行更精确的:
   • 胜负预测模型
   • 赔率分析
   • 球队表现评估
   • 趋势分析
""")

    # 显示API注册指南
    print_api_registration_guide()

    print("\n💡 建议:")
    print("1. 先注册免费API密钥获取真实数据")
    print("2. 然后我们就可以进行深入的数据分析和预测模型开发")
    print("3. 免费版的6个月数据足够训练一个不错的预测模型!")


if __name__ == "__main__":
    main()
