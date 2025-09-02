"""
Core domain models for the football prediction system.

This module defines the fundamental business entities and their relationships.
"""

from datetime import datetime
from enum import Enum
from typing import ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class MatchResult(str, Enum):
    """Match result types."""

    HOME_WIN = "H"
    DRAW = "D"
    AWAY_WIN = "A"


class MatchStatus(str, Enum):
    """Match status types."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class PredictionConfidence(str, Enum):
    """Prediction confidence levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Team(BaseModel):
    """Team domain model."""

    id: UUID = Field(default_factory=uuid4)
    external_api_id: int | None = Field(
        default=None, description="External API identifier"
    )
    name: str = Field(..., min_length=1, max_length=100)
    short_name: str = Field(..., min_length=1, max_length=10)
    tla: str = Field(default="", max_length=3, description="Three Letter Abbreviation")
    country: str = Field(default="Unknown", min_length=2, max_length=50)
    league: str = Field(default="Unknown", min_length=1, max_length=100)
    founded_year: int | None = None
    venue: str | None = None

    # Performance metrics
    current_form: list[MatchResult] = Field(default_factory=list, max_length=10)
    home_form: list[MatchResult] = Field(default_factory=list, max_length=5)
    away_form: list[MatchResult] = Field(default_factory=list, max_length=5)

    # Statistics
    goals_scored: int = Field(default=0, ge=0)
    goals_conceded: int = Field(default=0, ge=0)
    matches_played: int = Field(default=0, ge=0)
    wins: int = Field(default=0, ge=0)
    draws: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def points(self) -> int:
        """Calculate total points (3 for win, 1 for draw)."""
        return (self.wins * 3) + self.draws

    @property
    def goal_difference(self) -> int:
        """Calculate goal difference."""
        return self.goals_scored - self.goals_conceded

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.matches_played == 0:
            return 0.0
        return (self.wins / self.matches_played) * 100


class Match(BaseModel):
    """Match domain model."""

    id: UUID = Field(default_factory=uuid4)
    home_team_id: UUID
    away_team_id: UUID

    # Match details
    competition: str = Field(..., min_length=1, max_length=100)
    season: str = Field(..., min_length=4, max_length=20)
    matchday: int | None = Field(None, ge=1)

    # Scheduling
    scheduled_date: datetime
    kickoff_time: datetime | None = None
    venue: str | None = None

    # Status and result
    status: MatchStatus = MatchStatus.SCHEDULED
    result: MatchResult | None = None

    # Scores
    home_score: int | None = Field(None, ge=0)
    away_score: int | None = Field(None, ge=0)

    # Match statistics
    home_possession: float | None = Field(None, ge=0, le=100)
    away_possession: float | None = Field(None, ge=0, le=100)
    home_shots: int | None = Field(None, ge=0)
    away_shots: int | None = Field(None, ge=0)
    home_shots_on_target: int | None = Field(None, ge=0)
    away_shots_on_target: int | None = Field(None, ge=0)

    # Odds (if available)
    home_odds: float | None = Field(None, gt=0)
    draw_odds: float | None = Field(None, gt=0)
    away_odds: float | None = Field(None, gt=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("away_possession")
    @classmethod
    def validate_possession_sum(
        cls, v: float | None, info: ValidationInfo
    ) -> float | None:
        """Ensure possession percentages sum to 100."""
        if (
            v is not None
            and "home_possession" in info.data
            and info.data["home_possession"] is not None
        ):
            total = v + info.data["home_possession"]
            if abs(total - 100) > 1:  # Allow 1% tolerance for rounding
                raise ValueError(
                    "Possession percentages must sum to approximately 100%"
                )
        return v

    @property
    def is_finished(self) -> bool:
        """Check if match is finished."""
        return self.status == MatchStatus.FINISHED and self.result is not None


class Feature(BaseModel):
    """Feature data for ML models."""

    match_id: UUID
    feature_name: str = Field(..., min_length=1, max_length=100)
    feature_value: float | int | str | bool
    feature_type: str = Field(..., pattern=r"^(numerical|categorical|boolean)$")

    # Metadata
    extraction_method: str = Field(..., min_length=1, max_length=50)
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Quality metrics
    confidence_score: float | None = Field(None, ge=0, le=1)
    is_derived: bool = Field(default=False)
    source_features: list[str] = Field(default_factory=list)


class Prediction(BaseModel):
    """Prediction domain model."""

    id: UUID = Field(default_factory=uuid4)
    match_id: UUID
    model_version: str = Field(..., min_length=1, max_length=50)

    # Prediction results
    predicted_result: MatchResult
    home_win_probability: float = Field(..., ge=0, le=1)
    draw_probability: float = Field(..., ge=0, le=1)
    away_win_probability: float = Field(..., ge=0, le=1)

    # Confidence and quality
    confidence_level: PredictionConfidence
    confidence_score: float = Field(..., ge=0, le=1)

    # Expected scores (optional)
    expected_home_score: float | None = Field(None, ge=0)
    expected_away_score: float | None = Field(None, ge=0)

    # Model metadata
    features_used: list[str] = Field(default_factory=list)
    model_accuracy: float | None = Field(None, ge=0, le=1)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    prediction_date: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("draw_probability")
    @classmethod
    def validate_probability_sum(cls, v: float, info: ValidationInfo) -> float:
        """Ensure probabilities sum to 1."""
        if "home_win_probability" in info.data and "away_win_probability" in info.data:
            total = (
                v
                + info.data["home_win_probability"]
                + info.data["away_win_probability"]
            )
            if abs(total - 1.0) > 0.01:  # Allow 1% tolerance
                raise ValueError("Probabilities must sum to 1.0")
        return v

    @property
    def most_likely_result(self) -> MatchResult:
        """Get the most likely result based on probabilities."""
        probs = {
            MatchResult.HOME_WIN: self.home_win_probability,
            MatchResult.DRAW: self.draw_probability,
            MatchResult.AWAY_WIN: self.away_win_probability,
        }
        return max(probs, key=lambda k: probs[k])


class Model(BaseModel):
    """ML Model domain model."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., min_length=1, max_length=50)
    algorithm: str = Field(..., min_length=1, max_length=50)

    # Model metadata
    description: str | None = Field(None, max_length=500)
    hyperparameters: dict[str, str | int | float | bool] = Field(default_factory=dict)
    feature_names: list[str] = Field(default_factory=list)

    # Performance metrics
    accuracy: float | None = Field(None, ge=0, le=1)
    precision: float | None = Field(None, ge=0, le=1)
    recall: float | None = Field(None, ge=0, le=1)
    f1_score: float | None = Field(None, ge=0, le=1)
    roc_auc: float | None = Field(None, ge=0, le=1)
    log_loss: float | None = Field(None, ge=0)

    # Training metadata
    training_data_size: int | None = Field(None, ge=0)
    training_date: datetime | None = None
    validation_method: str | None = None

    # Status
    is_active: bool = Field(default=True)
    is_production: bool = Field(default=False)

    # File paths
    model_path: str | None = None
    metrics_path: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def performance_summary(self) -> dict[str, float | None]:
        """Get summary of model performance metrics."""
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "roc_auc": self.roc_auc,
            "log_loss": self.log_loss,
        }


class PredictionRequest(BaseModel):
    """Request model for making predictions."""

    match_id: UUID
    model_version: str | None = None
    include_probabilities: bool = Field(default=True)
    include_expected_scores: bool = Field(default=False)


class PredictionResponse(BaseModel):
    """Response model for predictions."""

    prediction: Prediction
    match_info: dict[str, str | datetime]
    model_info: dict[str, str | float]

    class Config:
        json_encoders: ClassVar = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions."""

    match_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    model_version: str | None = None
    include_probabilities: bool = Field(default=True)
    include_expected_scores: bool = Field(default=False)


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions."""

    predictions: list[PredictionResponse]
    total_count: int
    successful_predictions: int
    failed_predictions: int
    errors: list[dict[str, str]] = Field(default_factory=list)
