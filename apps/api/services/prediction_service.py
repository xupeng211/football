import logging
from typing import Any, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from apps.api.models import PredictionHistory
from models.predictor import Predictor

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(self) -> None:
        self._predictor: Optional[Predictor] = None

    def set_predictor(self, predictor: Predictor) -> None:
        """Sets the predictor instance for the service."""
        self._predictor = predictor

    def _get_predictor(self) -> Predictor:
        """Returns the active predictor, raising an error if it's not set."""
        if self._predictor is None:
            raise RuntimeError("Predictor is not initialized.")
        return self._predictor

    async def predict_async(
        self, request_data: dict, db: AsyncSession
    ) -> dict[str, Any]:
        """Generates predictions asynchronously and saves them to the database."""
        from fastapi.concurrency import run_in_threadpool

        predictor = self._get_predictor()

        # Run the CPU-bound prediction in a thread pool
        prediction_result = await run_in_threadpool(predictor.predict, request_data)

        # Save the prediction to the database
        await self.save_prediction_async(db, request_data, prediction_result)

        return prediction_result

    async def save_prediction_async(
        self, db: AsyncSession, request: dict, result: dict
    ) -> None:
        """Saves a prediction record to the database."""
        history_record = PredictionHistory(
            prediction_id=result["prediction_id"],
            home_team=request["home_team"],
            away_team=request["away_team"],
            match_date=request["match_date"],
            predicted_outcome=result["predicted_outcome"],
            confidence=result["confidence"],
        )
        db.add(history_record)
        await db.commit()

    def get_model_version(self) -> str | None:
        """Returns the version of the loaded model, if any."""
        if self._predictor:
            return self._predictor.model_version
        return None

    async def get_history_async(
        self, db: AsyncSession, limit: int, offset: int
    ) -> Sequence[PredictionHistory]:
        """Fetches prediction history from the database asynchronously."""
        result = await db.execute(select(PredictionHistory).offset(offset).limit(limit))
        return result.scalars().all()


# Instantiate the service to be used as a singleton
prediction_service = PredictionService()
