from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    prediction_id = Column(String, primary_key=True, index=True)
    home_team = Column(String, index=True)
    away_team = Column(String, index=True)
    match_date = Column(Date)
    predicted_outcome = Column(String)
    actual_outcome = Column(String, nullable=True)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
