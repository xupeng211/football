"""
Comprehensive tests for the domain services module to improve coverage.

Tests all major functionality including:
- PredictionService
- ModelService
- DataService
- Business logic validation
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from football_predict_system.core.exceptions import (InsufficientDataError, ModelNotFoundError, NotFoundError,
                                                     PredictionError)
from football_predict_system.domain.models import (BatchPredictionRequest, BatchPredictionResponse, Match, Model,
                                                   Prediction, PredictionRequest, PredictionResponse, Team)
from football_predict_system.domain.services import DataService, ModelService, PredictionService


class TestPredictionService:
    """Test PredictionService functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.service = PredictionService()

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test PredictionService initialization."""
        service = PredictionService()
        assert service.logger is not None

    @pytest.mark.asyncio
    async def test_generate_prediction_cache_hit(self):
        """Test prediction generation with cache hit."""
        request = PredictionRequest(
            match_id=uuid4(),
            model_version="v1.0"
        )

        cached_response = {
            "prediction": {
                "match_id": str(request.match_id),
                "home_win_probability": 0.6,
                "draw_probability": 0.25,
                "away_win_probability": 0.15,
                "confidence": 0.85,
                "model_version": "v1.0",
                "generated_at": "2023-01-01T12:00:00"
            },
            "match_info": {"home_team": "1", "away_team": "2"},
            "model_info": {"version": "v1.0", "accuracy": 0.85}
        }

        with patch('football_predict_system.domain.services.get_cache_manager') as mock_cache:
            mock_cache_manager = AsyncMock()
            mock_cache_manager.get.return_value = cached_response
            mock_cache.return_value = mock_cache_manager

            result = await self.service.generate_prediction(request)

            assert isinstance(result, PredictionResponse)
            assert result.prediction.match_id == request.match_id
            mock_cache_manager.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_prediction_cache_miss(self):
        """Test prediction generation with cache miss."""
        request = PredictionRequest(match_id=uuid4())

        # Mock dependencies
        mock_match = Match(
            id=request.match_id,
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            match_date=datetime.now() + timedelta(days=1),
            status="upcoming"
        )

        mock_model = Model(
            id=uuid4(),
            name="test_model",
            version="1.0",
            accuracy=0.85,
            created_at=datetime.now()
        )

        mock_prediction = Prediction(
            match_id=request.match_id,
            home_win_probability=0.6,
            draw_probability=0.25,
            away_win_probability=0.15,
            confidence=0.85,
            model_version="1.0",
            generated_at=datetime.now()
        )

        with patch.multiple(
            self.service,
            _get_match=AsyncMock(return_value=mock_match),
            _get_model=AsyncMock(return_value=mock_model),
            _extract_features=AsyncMock(return_value={"feature1": 1.0}),
            _predict_with_model=AsyncMock(return_value=mock_prediction),
        ), patch('football_predict_system.domain.services.get_cache_manager') as mock_cache:
            mock_cache_manager = AsyncMock()
            mock_cache_manager.get.return_value = None  # Cache miss
            mock_cache_manager.set.return_value = True
            mock_cache.return_value = mock_cache_manager

            result = await self.service.generate_prediction(request)

            assert isinstance(result, PredictionResponse)
            assert result.prediction.match_id == request.match_id
            mock_cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_prediction_match_not_found(self):
        """Test prediction generation when match not found."""
        request = PredictionRequest(match_id=uuid4())

        with patch.object(self.service, '_get_match', return_value=None), \
             patch('football_predict_system.domain.services.get_cache_manager') as mock_cache:

            mock_cache_manager = AsyncMock()
            mock_cache_manager.get.return_value = None
            mock_cache.return_value = mock_cache_manager

            with pytest.raises(NotFoundError) as exc_info:
                await self.service.generate_prediction(request)

            assert "match" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_prediction_model_not_found(self):
        """Test prediction generation when model not found."""
        request = PredictionRequest(match_id=uuid4(), model_version="nonexistent")

        mock_match = Match(
            id=request.match_id,
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            match_date=datetime.now() + timedelta(days=1),
            status="upcoming"
        )

        with patch.multiple(
            self.service,
            _get_match=AsyncMock(return_value=mock_match),
            _get_model=AsyncMock(return_value=None),
        ), patch('football_predict_system.domain.services.get_cache_manager') as mock_cache:

            mock_cache_manager = AsyncMock()
            mock_cache_manager.get.return_value = None
            mock_cache.return_value = mock_cache_manager

            with pytest.raises(ModelNotFoundError):
                await self.service.generate_prediction(request)

    @pytest.mark.asyncio
    async def test_generate_prediction_insufficient_data(self):
        """Test prediction generation with insufficient data."""
        request = PredictionRequest(match_id=uuid4())

        mock_match = Match(
            id=request.match_id,
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            match_date=datetime.now() + timedelta(days=1),
            status="upcoming"
        )

        mock_model = Model(
            id=uuid4(),
            name="test_model",
            version="1.0",
            accuracy=0.85,
            created_at=datetime.now()
        )

        with patch.multiple(
            self.service,
            _get_match=AsyncMock(return_value=mock_match),
            _get_model=AsyncMock(return_value=mock_model),
            _extract_features=AsyncMock(return_value=None),
        ), patch('football_predict_system.domain.services.get_cache_manager') as mock_cache:

            mock_cache_manager = AsyncMock()
            mock_cache_manager.get.return_value = None
            mock_cache.return_value = mock_cache_manager

            with pytest.raises(InsufficientDataError):
                await self.service.generate_prediction(request)

    @pytest.mark.asyncio
    async def test_generate_prediction_model_error(self):
        """Test prediction generation with model error."""
        request = PredictionRequest(match_id=uuid4())

        mock_match = Match(
            id=request.match_id,
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            match_date=datetime.now() + timedelta(days=1),
            status="upcoming"
        )

        mock_model = Model(
            id=uuid4(),
            name="test_model",
            version="1.0",
            accuracy=0.85,
            created_at=datetime.now()
        )

        with patch.multiple(
            self.service,
            _get_match=AsyncMock(return_value=mock_match),
            _get_model=AsyncMock(return_value=mock_model),
            _extract_features=AsyncMock(return_value={"feature1": 1.0}),
            _predict_with_model=AsyncMock(side_effect=Exception("Model error")),
        ), patch('football_predict_system.domain.services.get_cache_manager') as mock_cache:

            mock_cache_manager = AsyncMock()
            mock_cache_manager.get.return_value = None
            mock_cache.return_value = mock_cache_manager

            with pytest.raises(PredictionError):
                await self.service.generate_prediction(request)

    @pytest.mark.asyncio
    async def test_generate_batch_predictions(self):
        """Test batch prediction generation."""
        match_ids = [uuid4(), uuid4(), uuid4()]
        request = BatchPredictionRequest(
            match_ids=match_ids,
            model_version="v1.0"
        )

        # Mock individual predictions
        mock_predictions = []
        for match_id in match_ids:
            mock_prediction = PredictionResponse(
                prediction=Prediction(
                    match_id=match_id,
                    home_win_probability=0.6,
                    draw_probability=0.25,
                    away_win_probability=0.15,
                    confidence=0.85,
                    model_version="v1.0",
                    generated_at=datetime.now()
                ),
                match_info={"home_team": "1", "away_team": "2"},
                model_info={"version": "v1.0", "accuracy": 0.85}
            )
            mock_predictions.append(mock_prediction)

        with patch.object(self.service, 'generate_prediction', side_effect=mock_predictions):
            result = await self.service.generate_batch_predictions(request)

            assert isinstance(result, BatchPredictionResponse)
            assert len(result.predictions) == len(match_ids)
            assert result.batch_id is not None

    @pytest.mark.asyncio
    async def test_get_match_success(self):
        """Test successful match retrieval."""
        match_id = uuid4()
        mock_match = Match(
            id=match_id,
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            match_date=datetime.now() + timedelta(days=1),
            status="upcoming"
        )

        # This would normally be implemented to fetch from database
        with patch.object(self.service, '_fetch_match_from_db', return_value=mock_match):
            result = await self.service._get_match(match_id)
            assert result == mock_match

    @pytest.mark.asyncio
    async def test_get_model_success(self):
        """Test successful model retrieval."""
        model_version = "v1.0"
        mock_model = Model(
            id=uuid4(),
            name="test_model",
            version=model_version,
            accuracy=0.85,
            created_at=datetime.now()
        )

        # This would normally be implemented to fetch from model registry
        with patch.object(self.service, '_fetch_model_from_registry', return_value=mock_model):
            result = await self.service._get_model(model_version)
            assert result == mock_model

    @pytest.mark.asyncio
    async def test_extract_features_success(self):
        """Test successful feature extraction."""
        match = Match(
            id=uuid4(),
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            match_date=datetime.now() + timedelta(days=1),
            status="upcoming"
        )

        expected_features = {
            "home_team_recent_form": 0.7,
            "away_team_recent_form": 0.6,
            "head_to_head_ratio": 0.55
        }

        # This would normally be implemented to extract features
        with patch.object(self.service, '_compute_team_features', return_value=expected_features):
            result = await self.service._extract_features(match)
            assert result == expected_features


class TestModelService:
    """Test ModelService functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.service = ModelService()

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test ModelService initialization."""
        service = ModelService()
        assert service.logger is not None

    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models."""
        mock_models = [
            Model(
                id=uuid4(),
                name="model_1",
                version="1.0",
                accuracy=0.85,
                created_at=datetime.now()
            ),
            Model(
                id=uuid4(),
                name="model_2",
                version="2.0",
                accuracy=0.87,
                created_at=datetime.now()
            )
        ]

        with patch.object(self.service, '_fetch_models_from_registry', return_value=mock_models):
            result = await self.service.get_available_models()
            assert len(result) == 2
            assert all(isinstance(model, Model) for model in result)

    @pytest.mark.asyncio
    async def test_get_model_by_version(self):
        """Test getting model by version."""
        version = "v1.0"
        mock_model = Model(
            id=uuid4(),
            name="test_model",
            version=version,
            accuracy=0.85,
            created_at=datetime.now()
        )

        with patch.object(self.service, '_fetch_model_by_version', return_value=mock_model):
            result = await self.service.get_model_by_version(version)
            assert result == mock_model

    @pytest.mark.asyncio
    async def test_get_model_by_version_not_found(self):
        """Test getting model by version when not found."""
        version = "nonexistent"

        with patch.object(self.service, '_fetch_model_by_version', return_value=None):
            with pytest.raises(ModelNotFoundError):
                await self.service.get_model_by_version(version)


class TestDataService:
    """Test DataService functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.service = DataService()

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test DataService initialization."""
        service = DataService()
        assert service.logger is not None

    @pytest.mark.asyncio
    async def test_get_team_data(self):
        """Test getting team data."""
        team_id = uuid4()
        mock_team = Team(
            id=team_id,
            name="Test Team",
            league="Premier League",
            country="England",
            founded_year=1900
        )

        with patch.object(self.service, '_fetch_team_from_db', return_value=mock_team):
            result = await self.service.get_team_data(team_id)
            assert result == mock_team

    @pytest.mark.asyncio
    async def test_get_team_data_not_found(self):
        """Test getting team data when not found."""
        team_id = uuid4()

        with patch.object(self.service, '_fetch_team_from_db', return_value=None):
            with pytest.raises(NotFoundError):
                await self.service.get_team_data(team_id)

    @pytest.mark.asyncio
    async def test_get_match_history(self):
        """Test getting match history."""
        team_id = uuid4()
        limit = 10

        mock_matches = [
            Match(
                id=uuid4(),
                home_team_id=team_id,
                away_team_id=uuid4(),
                match_date=datetime.now() - timedelta(days=7),
                status="completed"
            )
            for _ in range(5)
        ]

        with patch.object(self.service, '_fetch_team_matches', return_value=mock_matches):
            result = await self.service.get_match_history(team_id, limit)
            assert len(result) == 5
            assert all(isinstance(match, Match) for match in result)

    @pytest.mark.asyncio
    async def test_get_head_to_head_record(self):
        """Test getting head-to-head record."""
        team1_id = uuid4()
        team2_id = uuid4()

        mock_matches = [
            Match(
                id=uuid4(),
                home_team_id=team1_id,
                away_team_id=team2_id,
                match_date=datetime.now() - timedelta(days=30),
                status="completed"
            )
            for _ in range(3)
        ]

        with patch.object(self.service, '_fetch_head_to_head_matches', return_value=mock_matches):
            result = await self.service.get_head_to_head_record(team1_id, team2_id)
            assert len(result) == 3
            assert all(isinstance(match, Match) for match in result)

    @pytest.mark.asyncio
    async def test_validate_match_data(self):
        """Test match data validation."""
        valid_match = Match(
            id=uuid4(),
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            match_date=datetime.now() + timedelta(days=1),
            status="upcoming"
        )

        # Valid match should pass validation
        result = await self.service.validate_match_data(valid_match)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_match_data_invalid(self):
        """Test match data validation with invalid data."""
        invalid_match = Match(
            id=uuid4(),
            home_team_id=uuid4(),
            away_team_id=uuid4(),
            match_date=datetime.now() - timedelta(days=1),  # Past date
            status="upcoming"  # But status says upcoming
        )

        # Invalid match should fail validation
        with pytest.raises(ValueError):
            await self.service.validate_match_data(invalid_match)


if __name__ == "__main__":
    pytest.main([__file__])
