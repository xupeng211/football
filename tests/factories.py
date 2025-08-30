"""
测试数据工厂
提供统一的测试数据生成，减少硬编码数据
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class MatchData:
    """比赛数据结构"""

    home_team: str
    away_team: str
    match_date: str
    home_odds: float
    draw_odds: float
    away_odds: float
    home_form: float = 0.0
    away_form: float = 0.0


class TestDataFactory:
    """测试数据工厂类"""

    # 常用球队名称
    TEAMS = [
        "Barcelona",
        "Real Madrid",
        "Manchester United",
        "Liverpool",
        "Bayern Munich",
        "PSG",
        "Juventus",
        "Chelsea",
        "Arsenal",
        "Tottenham",
    ]

    @classmethod
    def create_match_data(
        self, home_team: Optional[str] = None, away_team: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """创建单场比赛数据"""
        if not home_team:
            home_team = random.choice(self.TEAMS)
        if not away_team:
            away_team = random.choice([t for t in self.TEAMS if t != home_team])

        default_data = {
            "home_team": home_team,
            "away_team": away_team,
            "match_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "home_odds": round(random.uniform(1.5, 4.0), 2),
            "draw_odds": round(random.uniform(2.8, 4.5), 2),
            "away_odds": round(random.uniform(1.5, 4.0), 2),
            "home_form": round(random.uniform(0.0, 3.0), 1),
            "away_form": round(random.uniform(0.0, 3.0), 1),
        }

        # 合并用户提供的参数
        default_data.update(kwargs)
        return default_data

    @classmethod
    def create_batch_matches(self, count: int = 5) -> List[Dict[str, Any]]:
        """创建批量比赛数据"""
        matches = []
        used_pairs = set()

        for _ in range(count):
            while True:
                home = random.choice(self.TEAMS)
                away = random.choice([t for t in self.TEAMS if t != home])
                pair = (home, away)

                if pair not in used_pairs:
                    used_pairs.add(pair)
                    matches.append(self.create_match_data(home, away))
                    break

        return matches

    @classmethod
    def create_prediction_response(
        self,
        home_win: Optional[float] = None,
        draw: Optional[float] = None,
        away_win: Optional[float] = None,
    ) -> Dict[str, Any]:
        """创建预测响应数据"""
        if not all([home_win, draw, away_win]):
            # 生成随机概率，确保总和为1
            probs = [random.random() for _ in range(3)]
            total = sum(probs)
            home_win, draw, away_win = (p / total for p in probs)

        # 确定预测结果
        max_prob = max(home_win, draw, away_win)
        if max_prob == home_win:
            predicted_outcome = "home_win"
        elif max_prob == draw:
            predicted_outcome = "draw"
        else:
            predicted_outcome = "away_win"

        return {
            "home_win": round(home_win, 3),
            "draw": round(draw, 3),
            "away_win": round(away_win, 3),
            "predicted_outcome": predicted_outcome,
            "confidence": round(max_prob, 3),
            "prediction_id": f"pred_{random.randint(1000, 9999)}",
        }

    @classmethod
    def create_health_response(
        self,
        status: str = "healthy",
        db_status: bool = True,
        redis_status: bool = True,
        prefect_status: bool = True,
    ) -> Dict[str, Any]:
        """创建健康检查响应数据"""
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "database": "healthy" if db_status else "unhealthy",
                "redis": "healthy" if redis_status else "unhealthy",
                "prefect": "healthy" if prefect_status else "unhealthy",
            },
        }

    @classmethod
    def create_dataframe_sample(self, rows: int = 100) -> pd.DataFrame:
        """创建示例DataFrame用于测试"""
        data = []
        for i in range(rows):
            match = self.create_match_data()
            # 添加一些额外的特征列
            match.update(
                {
                    "match_id": f"match_{i + 1:04d}",
                    "league": random.choice(
                        ["Premier League", "La Liga", "Bundesliga"]
                    ),
                    "season": "2024-25",
                    "home_goals": random.randint(0, 5),
                    "away_goals": random.randint(0, 5),
                }
            )
            data.append(match)

        return pd.DataFrame(data)


# 便捷函数
def sample_match(**kwargs) -> Dict[str, Any]:
    """快速创建单场比赛数据"""
    return TestDataFactory.create_match_data(**kwargs)


def sample_matches(count: int = 5) -> List[Dict[str, Any]]:
    """快速创建批量比赛数据"""
    return TestDataFactory.create_batch_matches(count)


def sample_prediction(**kwargs) -> Dict[str, Any]:
    """快速创建预测响应数据"""
    return TestDataFactory.create_prediction_response(**kwargs)


def sample_health(**kwargs) -> Dict[str, Any]:
    """快速创建健康检查响应数据"""
    return TestDataFactory.create_health_response(**kwargs)
