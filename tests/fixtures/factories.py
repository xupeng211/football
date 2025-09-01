"""
测试数据工厂

提供生成测试数据的工厂函数。
"""

import uuid
from datetime import datetime, timedelta
from typing import Any


class MatchFactory:
    """比赛数据工厂"""

    @staticmethod
    def create(
        match_id: str | None = None,
        home_team_id: str | None = None,
        away_team_id: str | None = None,
        date: datetime | None = None,
        status: str = "scheduled",
        **kwargs,
    ) -> dict[str, Any]:
        """创建比赛数据"""
        return {
            "id": match_id or str(uuid.uuid4()),
            "home_team_id": home_team_id or str(uuid.uuid4()),
            "away_team_id": away_team_id or str(uuid.uuid4()),
            "date": date or datetime.utcnow() + timedelta(days=1),
            "status": status,
            "league": kwargs.get("league", "Premier League"),
            "season": kwargs.get("season", "2024-25"),
            "round": kwargs.get("round", 1),
            **kwargs,
        }

    @staticmethod
    def create_batch(count: int = 5) -> list[dict[str, Any]]:
        """批量创建比赛数据"""
        return [MatchFactory.create() for _ in range(count)]


class TeamFactory:
    """球队数据工厂"""

    @staticmethod
    def create(
        team_id: str | None = None,
        name: str | None = None,
        league: str = "Premier League",
        country: str = "England",
        **kwargs,
    ) -> dict[str, Any]:
        """创建球队数据"""
        team_names = [
            "Manchester United",
            "Liverpool",
            "Arsenal",
            "Chelsea",
            "Manchester City",
            "Tottenham",
            "Newcastle",
            "Brighton",
        ]

        return {
            "id": team_id or str(uuid.uuid4()),
            "name": name or team_names[len(team_id or "") % len(team_names)],
            "league": league,
            "country": country,
            "founded": kwargs.get("founded", 1878),
            "stadium": kwargs.get("stadium", f"{name or 'Test'} Stadium"),
            **kwargs,
        }

    @staticmethod
    def create_batch(count: int = 10) -> list[dict[str, Any]]:
        """批量创建球队数据"""
        return [TeamFactory.create() for _ in range(count)]


class PredictionFactory:
    """预测数据工厂"""

    @staticmethod
    def create(
        prediction_id: str | None = None,
        match_id: str | None = None,
        home_win_prob: float = 0.45,
        draw_prob: float = 0.30,
        away_win_prob: float = 0.25,
        confidence: float = 0.85,
        **kwargs,
    ) -> dict[str, Any]:
        """创建预测数据"""
        return {
            "id": prediction_id or str(uuid.uuid4()),
            "match_id": match_id or str(uuid.uuid4()),
            "home_win_probability": home_win_prob,
            "draw_probability": draw_prob,
            "away_win_probability": away_win_prob,
            "confidence": confidence,
            "model_name": kwargs.get("model_name", "xgboost_v1"),
            "model_version": kwargs.get("model_version", "1.0.0"),
            "created_at": kwargs.get("created_at", datetime.utcnow()),
            **kwargs,
        }

    @staticmethod
    def create_batch(count: int = 20) -> list[dict[str, Any]]:
        """批量创建预测数据"""
        return [PredictionFactory.create() for _ in range(count)]


class UserFactory:
    """用户数据工厂"""

    @staticmethod
    def create(
        user_id: str | None = None,
        username: str | None = None,
        email: str | None = None,
        is_active: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """创建用户数据"""
        return {
            "id": user_id or str(uuid.uuid4()),
            "username": username or f"testuser_{uuid.uuid4().hex[:8]}",
            "email": email or f"test_{uuid.uuid4().hex[:8]}@example.com",
            "is_active": is_active,
            "role": kwargs.get("role", "user"),
            "created_at": kwargs.get("created_at", datetime.utcnow()),
            **kwargs,
        }


class ModelFactory:
    """模型数据工厂"""

    @staticmethod
    def create(
        model_id: str | None = None,
        name: str = "xgboost_v1",
        version: str = "1.0.0",
        accuracy: float = 0.85,
        **kwargs,
    ) -> dict[str, Any]:
        """创建模型数据"""
        return {
            "id": model_id or str(uuid.uuid4()),
            "name": name,
            "version": version,
            "accuracy": accuracy,
            "precision": kwargs.get("precision", 0.82),
            "recall": kwargs.get("recall", 0.88),
            "f1_score": kwargs.get("f1_score", 0.85),
            "training_date": kwargs.get("training_date", datetime.utcnow()),
            "is_active": kwargs.get("is_active", True),
            **kwargs,
        }


class APIResponseFactory:
    """API响应数据工厂"""

    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> dict[str, Any]:
        """创建成功响应"""
        return {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def error_response(
        error_code: str = "VALIDATION_ERROR",
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建错误响应"""
        return {
            "status": "error",
            "error_code": error_code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }


# 便捷的测试数据集合
class TestDataSets:
    """预定义的测试数据集合"""

    @staticmethod
    def premier_league_match() -> dict[str, Any]:
        """英超比赛数据"""
        home_team = TeamFactory.create(
            name="Manchester United", league="Premier League"
        )
        away_team = TeamFactory.create(name="Liverpool", league="Premier League")
        match = MatchFactory.create(
            home_team_id=home_team["id"],
            away_team_id=away_team["id"],
            league="Premier League",
        )
        prediction = PredictionFactory.create(match_id=match["id"])

        return {
            "home_team": home_team,
            "away_team": away_team,
            "match": match,
            "prediction": prediction,
        }

    @staticmethod
    def upcoming_matches(count: int = 5) -> list[dict[str, Any]]:
        """即将到来的比赛"""
        matches = []
        for i in range(count):
            match_data = TestDataSets.premier_league_match()
            match_data["match"]["date"] = datetime.utcnow() + timedelta(days=i + 1)
            matches.append(match_data)
        return matches
