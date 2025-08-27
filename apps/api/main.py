"""
足球预测API服务

提供足球比赛结果预测的REST API接口
"""

from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from apps.api.routers import health, metrics, predictions
from models.predictor import create_predictor


# Pydantic模型定义
class MatchInput(BaseModel):
    """单场比赛输入"""

    home: str = Field(..., description="主队名称")
    away: str = Field(..., description="客队名称")
    home_form: float = Field(default=1.5, description="主队状态")
    away_form: float = Field(default=1.5, description="客队状态")
    odds_h: float = Field(default=2.0, description="主胜赔率")
    odds_d: float = Field(default=3.0, description="平局赔率")
    odds_a: float = Field(default=3.0, description="客胜赔率")


class PredictionOutput(BaseModel):
    """预测结果输出"""

    model_config = {"protected_namespaces": ()}

    home_win: float = Field(..., description="主胜概率")
    draw: float = Field(..., description="平局概率")
    away_win: float = Field(..., description="客胜概率")
    predicted_outcome: str = Field(
        ..., description="预测结果 (home_win, draw, away_win)"
    )
    confidence: float = Field(..., description="预测置信度")
    model_version: str = Field(..., description="模型版本")


class VersionResponse(BaseModel):
    """版本信息响应"""

    model_config = {"protected_namespaces": ()}

    api_version: str
    model_version: str
    model_info: dict[str, Any]


# 创建FastAPI应用
app = FastAPI(title="足球预测API", description="足球比赛结果预测服务", version="1.0.0")
app.include_router(predictions.router)
app.include_router(health.router)
app.include_router(metrics.router)

# 全局预测器实例
predictor = None


@app.on_event("startup")
async def startup_event() -> None:
    """应用启动时初始化预测器"""
    global predictor
    try:
        predictor = create_predictor()
        if predictor.model is None:
            print("警告: 未找到模型文件,API将使用默认预测")
    except Exception as e:
        print(f"预测器初始化失败: {e}")


@app.get("/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """获取版本信息"""
    model_info: dict[str, Any] = {}
    model_version = "unknown"

    if predictor and predictor.model is not None:
        model_info = predictor.get_model_info()
        model_version = predictor.model_version or "unknown"

    return VersionResponse(
        api_version="1.0.0", model_version=model_version, model_info=model_info
    )


@app.post("/predict", response_model=list[PredictionOutput])
async def predict_matches(matches: list[MatchInput]) -> list[PredictionOutput]:
    """
    批量预测比赛结果

    Args:
        matches: 比赛列表

    Returns:
        List[PredictionOutput]: 预测结果列表
    """
    if not matches:
        raise HTTPException(status_code=400, detail="比赛列表不能为空")

    if len(matches) > 100:
        raise HTTPException(status_code=400, detail="单次请求最多支持100场比赛")

    try:
        # 转换输入格式
        match_data = []
        for match in matches:
            match_dict = {
                "home": match.home,
                "away": match.away,
                "h": match.odds_h,
                "d": match.odds_d,
                "a": match.odds_a,
                "team_stats": {
                    "home_form": match.home_form,
                    "away_form": match.away_form,
                },
            }
            match_data.append(match_dict)

        # 进行预测
        if predictor and predictor.model is not None:
            predictions = predictor.predict_batch(match_data)
        else:
            # 如果模型未加载,返回默认预测
            predictions = []
            for _ in matches:
                predictions.append(
                    {
                        "home_win": 0.33,
                        "draw": 0.34,
                        "away_win": 0.33,
                        "model_version": "default",
                    }
                )

        # 转换输出格式
        results = []
        for pred in predictions:
            results.append(
                PredictionOutput(
                    home_win=float(pred["home_win"]),
                    draw=float(pred["draw"]),
                    away_win=float(pred["away_win"]),
                    predicted_outcome=str(pred.get("predicted_outcome", "unknown")),
                    confidence=float(pred.get("confidence", 0.0)),
                    model_version=str(pred.get("model_version", "unknown")),
                )
            )

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {e!s}") from None


@app.get("/")
async def root() -> dict[str, str]:
    """根路径"""
    return {
        "message": "足球预测API服务",
        "docs": "/docs",
        "health": "/health",
        "version": "/version",
    }


if __name__ == "__main__":
    # 开发模式运行
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
