"""
预测API路由
"""

from datetime import date, datetime
from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from apps.api.services.prediction_service import prediction_service

logger = structlog.get_logger()
router = APIRouter()


# 请求/响应模型
class PredictionRequest(BaseModel):
    """预测请求模型"""

    pass


class SingleMatchPredictionRequest(BaseModel):
    """单场比赛预测请求"""

    home_team: str = Field(..., description="主队名称", examples=["Arsenal"])
    away_team: str = Field(..., description="客队名称", examples=["Chelsea"])
    match_date: date = Field(..., description="比赛日期", examples=["2025-08-30"])
    home_odds: float = Field(..., description="主胜赔率", gt=1.0, examples=[2.1])
    draw_odds: float = Field(..., description="平局赔率", gt=1.0, examples=[3.3])
    away_odds: float = Field(..., description="客胜赔率", gt=1.0, examples=[3.2])


class BatchMatchPredictionRequest(BaseModel):
    """批量比赛预测请求"""

    matches: list[SingleMatchPredictionRequest] = Field(
        ..., description="比赛列表", min_length=1
    )


class PredictionResponse(BaseModel):
    """预测响应模型"""

    prediction_id: str = Field(..., description="预测ID")
    home_team: str = Field(..., description="主队")
    away_team: str = Field(..., description="客队")
    match_date: date = Field(..., description="比赛日期")
    predicted_outcome: str = Field(..., description="预测结果")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    created_at: datetime = Field(..., description="创建时间")


class BatchPredictionResponse(BaseModel):
    """批量预测响应模型"""

    predictions: list[PredictionResponse] = Field(..., description="预测结果列表")
    total_matches: int = Field(..., description="总比赛数")
    processed_at: datetime = Field(..., description="处理时间")


# API路由
@router.post("/predict/single", response_model=PredictionResponse)
async def predict_single_match(
    request: SingleMatchPredictionRequest,
    model_name: str | None = Query(None, description="用于预测的模型名称"),
) -> PredictionResponse:
    """
    单场比赛预测
    """
    try:
        prediction_id = str(uuid4())

        # 1. Get Prediction
        probabilities = prediction_service.predict(
            request.model_dump(), model_name=model_name
        )
        # Probabilities are for [Home, Draw, Away]
        outcome_map = {0: "home_win", 1: "draw", 2: "away_win"}
        predicted_index = probabilities[0].argmax()
        predicted_outcome = outcome_map[predicted_index]
        confidence = float(probabilities[0].max())

        # 3. Format Response
        response = PredictionResponse(
            prediction_id=prediction_id,
            home_team=request.home_team,
            away_team=request.away_team,
            match_date=request.match_date,
            predicted_outcome=predicted_outcome,
            confidence=confidence,
            created_at=datetime.now(),
        )

        logger.info(
            "单场比赛预测完成",
            prediction_id=prediction_id,
            home_team=request.home_team,
            away_team=request.away_team,
        )

        return response

    except Exception as e:
        logger.error("单场比赛预测失败", error=str(e))
        raise HTTPException(status_code=500, detail="预测服务暂时不可用")


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch_matches(
    request: BatchMatchPredictionRequest,
    model_name: str | None = Query(None, description="用于预测的模型名称"),
) -> BatchPredictionResponse:
    """
    批量比赛预测
    """
    try:
        predictions = []
        outcome_map = {0: "home_win", 1: "draw", 2: "away_win"}

        matches_data = [match.model_dump() for match in request.matches]
        if not matches_data:
            return BatchPredictionResponse(
                predictions=[],
                total_matches=0,
                processed_at=datetime.now(),
            )

        all_probabilities = prediction_service.predict_batch(
            matches_data, model_name=model_name
        )

        for i, match in enumerate(request.matches):
            prediction_id = str(uuid4())
            probabilities = all_probabilities[i]
            predicted_index = probabilities.argmax()
            predicted_outcome = outcome_map[predicted_index]
            confidence = float(probabilities.max())

            prediction = PredictionResponse(
                prediction_id=prediction_id,
                home_team=match.home_team,
                away_team=match.away_team,
                match_date=match.match_date,
                predicted_outcome=predicted_outcome,
                confidence=confidence,
                created_at=datetime.now(),
            )
            predictions.append(prediction)

        response = BatchPredictionResponse(
            predictions=predictions,
            total_matches=len(request.matches),
            processed_at=datetime.now(),
        )

        logger.info("批量预测完成", total_matches=len(request.matches))

        return response

    except Exception as e:
        logger.error("批量预测失败", error=str(e))
        raise HTTPException(status_code=500, detail="批量预测服务暂时不可用")


@router.get("/history")
async def get_prediction_history(
    limit: int = Query(default=10, ge=1, le=100, description="返回结果数量限制"),
    offset: int = Query(default=0, ge=0, description="结果偏移量"),
) -> dict[str, Any]:
    """
    获取预测历史记录
    """
    try:
        # 这里应该从数据库查询历史记录
        # history = await prediction_service.get_history(
        #     limit=limit, offset=offset
        # )

        # 临时返回模拟数据
        mock_history = [
            {
                "prediction_id": str(uuid4()),
                "home_team": "曼城",
                "away_team": "利物浦",
                "match_date": "2024-03-15",
                "predicted_outcome": "home_win",
                "actual_outcome": "draw",
                "confidence": 0.82,
                "created_at": "2024-03-14T10:30:00Z",
            },
            {
                "prediction_id": str(uuid4()),
                "home_team": "阿森纳",
                "away_team": "切尔西",
                "match_date": "2024-03-14",
                "predicted_outcome": "away_win",
                "actual_outcome": "away_win",
                "confidence": 0.71,
                "created_at": "2024-03-13T15:45:00Z",
            },
        ]

        response = {
            "predictions": mock_history[:limit],
            "total_count": len(mock_history),
            "limit": limit,
            "offset": offset,
        }

        logger.info("预测历史查询完成", limit=limit, offset=offset)

        return response

    except Exception as e:
        logger.error("获取预测历史失败", error=str(e))
        raise HTTPException(status_code=500, detail="历史记录服务暂时不可用")
