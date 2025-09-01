"""
预测API路由
"""

from datetime import date, datetime
from typing import Sequence
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.models import PredictionHistory
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
    db: AsyncSession = Depends(get_db),
    model_name: str | None = Query(None, description="用于预测的模型名称"),
) -> PredictionResponse:
    """
    单场比赛预测
    """
    try:
        prediction_id = str(uuid4())
        request_data = request.model_dump()
        request_data["prediction_id"] = prediction_id

        prediction_result = await prediction_service.predict_async(request_data, db)

        predicted_outcome = prediction_result.get("predicted_outcome", "unknown")
        confidence = prediction_result.get("confidence", 0.0)

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
    db: AsyncSession = Depends(get_db),
    model_name: str | None = Query(None, description="用于预测的模型名称"),
) -> BatchPredictionResponse:
    """
    批量比赛预测
    """
    import asyncio

    async def process_match(
        match_request: SingleMatchPredictionRequest,
    ) -> PredictionResponse:
        prediction_id = str(uuid4())
        request_data = match_request.model_dump()
        request_data["prediction_id"] = prediction_id

        prediction_result = await prediction_service.predict_async(request_data, db)

        return PredictionResponse(
            prediction_id=prediction_id,
            home_team=match_request.home_team,
            away_team=match_request.away_team,
            match_date=match_request.match_date,
            predicted_outcome=prediction_result.get("predicted_outcome", "unknown"),
            confidence=prediction_result.get("confidence", 0.0),
            created_at=datetime.now(),
        )

    try:
        tasks = [process_match(match) for match in request.matches]
        predictions = await asyncio.gather(*tasks)

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


@router.get("/history", response_model=list[PredictionResponse])
async def get_prediction_history(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=100, description="返回结果数量限制"),
    offset: int = Query(default=0, ge=0, description="结果偏移量"),
) -> Sequence[PredictionHistory]:
    """
    获取预测历史记录
    """
    try:
        history = await prediction_service.get_history_async(
            db, limit=limit, offset=offset
        )
        logger.info("预测历史查询完成", limit=limit, offset=offset, count=len(history))
        return history

    except Exception as e:
        logger.error("获取预测历史失败", error=str(e))
        raise HTTPException(status_code=500, detail="历史记录服务暂时不可用")
