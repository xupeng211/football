"""Comprehensive tests for domain services."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from football_predict_system.core.exceptions import (
    InsufficientDataError,
    ModelNotFoundError,
    NotFoundError,
    PredictionError,
)
from football_predict_system.domain.models import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    Match,
    MatchResult,
    Model,
    ModelStatus,
    ModelType,
    Prediction,
    PredictionConfidence,
    PredictionRequest,
    PredictionResponse,
    Team,
)
from football_predict_system.domain.services import (
    AnalyticsService,
    DataService,
    ModelService,
    PredictionService,
    analytics_service,
    data_service,
    model_service,
    prediction_service,
)


@pytest.fixture
def mock_match():
    """Create a mock match."""
    return Match(
        id=uuid4(),
        home_team_id=uuid4(),
        away_team_id=uuid4(),
        scheduled_date=datetime.utcnow(),
        competition="Premier League",
        season="2024-25",
        status="scheduled"
    )


@pytest.fixture
def mock_model():
    """Create a mock model."""
    return Model(
        id=uuid4(),
        name="test_model",
        version="v1.0.0",
        type=ModelType.XGBOOST,
        status=ModelStatus.ACTIVE,
        accuracy=0.85,
        is_production=True,
        is_active=True
    )


@pytest.fixture
def mock_team():
    """Create a mock team."""
    return Team(
        id=uuid4(),
        name="Arsenal",
        code="ARS",
        founded=1886,
        country="England",
        stadium="Emirates Stadium"
    )


@pytest.fixture
def mock_prediction():
    """Create a mock prediction."""
    return Prediction(
        id=uuid4(),
        match_id=uuid4(),
        model_version="v1.0.0",
        predicted_result=MatchResult.HOME_WIN,
        home_win_probability=0.5,
        draw_probability=0.3,
        away_win_probability=0.2,
        confidence_level=PredictionConfidence.MEDIUM,
        confidence_score=0.75,
        created_at=datetime.utcnow()
    )


class TestPredictionService:
    """Test PredictionService class."""

    def test_prediction_service_initialization(self):
        """Test PredictionService initialization."""
        service = PredictionService()
        assert service.logger is not None

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_generate_prediction_from_cache(self, mock_cache, mock_match):
        """Test prediction generation from cache."""
        service = PredictionService()

        # Setup cache mock
        cache_manager = AsyncMock()
        cached_prediction = {
            "prediction": {
                "id": str(uuid4()),
                "match_id": str(mock_match.id),
                "predicted_result": "HOME_WIN",
                "confidence_score": 0.85
            },
            "match_info": {},
            "model_info": {}
        }
        cache_manager.get.return_value = cached_prediction
        mock_cache.return_value = cache_manager

        request = PredictionRequest(
            match_id=mock_match.id,
            model_version="v1.0.0"
        )

        result = await service.generate_prediction(request)

        assert isinstance(result, PredictionResponse)
        cache_manager.get.assert_called_once()

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_generate_prediction_match_not_found(self, mock_cache):
        """Test prediction when match not found."""
        service = PredictionService()

        # Setup mocks
        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        mock_cache.return_value = cache_manager

        service._get_match = AsyncMock(return_value=None)

        request = PredictionRequest(
            match_id=uuid4(),
            model_version="v1.0.0"
        )

        with pytest.raises(NotFoundError):
            await service.generate_prediction(request)

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_generate_prediction_model_not_found(self, mock_cache, mock_match):
        """Test prediction when model not found."""
        service = PredictionService()

        # Setup mocks
        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        mock_cache.return_value = cache_manager

        service._get_match = AsyncMock(return_value=mock_match)
        service._get_model = AsyncMock(return_value=None)

        request = PredictionRequest(
            match_id=mock_match.id,
            model_version="v1.0.0"
        )

        with pytest.raises(ModelNotFoundError):
            await service.generate_prediction(request)

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_generate_prediction_insufficient_data(self, mock_cache,
                                                         mock_match, mock_model):
        """Test prediction with insufficient data."""
        service = PredictionService()

        # Setup mocks
        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        mock_cache.return_value = cache_manager

        service._get_match = AsyncMock(return_value=mock_match)
        service._get_model = AsyncMock(return_value=mock_model)
        service._extract_features = AsyncMock(return_value=None)

        request = PredictionRequest(match_id=mock_match.id)

        with pytest.raises(InsufficientDataError):
            await service.generate_prediction(request)

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_generate_prediction_success(self, mock_cache, mock_match,
                                              mock_model, mock_prediction):
        """Test successful prediction generation."""
        service = PredictionService()

        # Setup mocks
        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True
        mock_cache.return_value = cache_manager

        service._get_match = AsyncMock(return_value=mock_match)
        service._get_model = AsyncMock(return_value=mock_model)
        service._extract_features = AsyncMock(return_value={"feature1": 0.5})
        service._predict_with_model = AsyncMock(return_value=mock_prediction)

        request = PredictionRequest(match_id=mock_match.id)

        result = await service.generate_prediction(request)

        assert isinstance(result, PredictionResponse)
        assert result.prediction == mock_prediction
        assert "home_team" in result.match_info
        assert "name" in result.model_info
        cache_manager.set.assert_called_once()

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_generate_prediction_service_error(self, mock_cache,
                                                     mock_match, mock_model):
        """Test prediction service error handling."""
        service = PredictionService()

        # Setup mocks
        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        mock_cache.return_value = cache_manager

        service._get_match = AsyncMock(return_value=mock_match)
        service._get_model = AsyncMock(return_value=mock_model)
        service._extract_features = AsyncMock(return_value={"feature1": 0.5})
        service._predict_with_model = AsyncMock(
            side_effect=Exception("Model error")
        )

        request = PredictionRequest(match_id=mock_match.id)

        with pytest.raises(PredictionError):
            await service.generate_prediction(request)

    @pytest.mark.asyncio
    async def test_generate_batch_predictions_success(self, mock_match):
        """Test successful batch prediction generation."""
        service = PredictionService()

        # Mock the single prediction method
        mock_response = PredictionResponse(
            prediction=Prediction(
                id=uuid4(),
                match_id=mock_match.id,
                model_version="v1.0.0",
                predicted_result=MatchResult.HOME_WIN,
                confidence_score=0.75,
                created_at=datetime.utcnow()
            ),
            match_info={},
            model_info={}
        )

        service._safe_generate_prediction = AsyncMock(return_value=mock_response)

        request = BatchPredictionRequest(
            match_ids=[uuid4(), uuid4(), uuid4()],
            model_version="v1.0.0"
        )

        result = await service.generate_batch_predictions(request)

        assert isinstance(result, BatchPredictionResponse)
        assert result.total_count == 3
        assert result.successful_predictions == 3
        assert result.failed_predictions == 0
        assert len(result.predictions) == 3
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_generate_batch_predictions_with_errors(self):
        """Test batch predictions with some errors."""
        service = PredictionService()

        # Mock the single prediction method to return success and error
        def side_effect(request):
            if str(request.match_id).endswith('1'):
                raise Exception("Test error")
            return PredictionResponse(
                prediction=Prediction(
                    id=uuid4(),
                    match_id=request.match_id,
                    model_version="v1.0.0",
                    predicted_result=MatchResult.HOME_WIN,
                    confidence_score=0.75,
                    created_at=datetime.utcnow()
                ),
                match_info={},
                model_info={}
            )

        service._safe_generate_prediction = AsyncMock(side_effect=side_effect)

        match_ids = [uuid4(), uuid4()]
        match_ids[1] = UUID(str(match_ids[1])[:-1] + '1')  # Make it end with '1'

        request = BatchPredictionRequest(
            match_ids=match_ids,
            model_version="v1.0.0"
        )

        result = await service.generate_batch_predictions(request)

        assert result.total_count == 2
        assert result.successful_predictions == 1
        assert result.failed_predictions == 1
        assert len(result.predictions) == 1
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_safe_generate_prediction_success(self, mock_match):
        """Test safe prediction generation success."""
        service = PredictionService()

        mock_response = PredictionResponse(
            prediction=Prediction(
                id=uuid4(),
                match_id=mock_match.id,
                model_version="v1.0.0",
                predicted_result=MatchResult.HOME_WIN,
                confidence_score=0.75,
                created_at=datetime.utcnow()
            ),
            match_info={},
            model_info={}
        )

        service.generate_prediction = AsyncMock(return_value=mock_response)

        request = PredictionRequest(match_id=mock_match.id)
        result = await service._safe_generate_prediction(request)

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_safe_generate_prediction_error(self, mock_match):
        """Test safe prediction generation error handling."""
        service = PredictionService()

        service.generate_prediction = AsyncMock(
            side_effect=Exception("Test error")
        )

        request = PredictionRequest(match_id=mock_match.id)
        result = await service._safe_generate_prediction(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_match_placeholder(self):
        """Test _get_match placeholder method."""
        service = PredictionService()
        result = await service._get_match(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_model_placeholder(self):
        """Test _get_model placeholder method."""
        service = PredictionService()
        result = await service._get_model("v1.0.0")
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_features_placeholder(self, mock_match):
        """Test _extract_features placeholder method."""
        service = PredictionService()
        result = await service._extract_features(mock_match)
        assert result == {}

    @pytest.mark.asyncio
    async def test_predict_with_model(self, mock_model, mock_match):
        """Test _predict_with_model placeholder method."""
        service = PredictionService()
        features = {"feature1": 0.5}

        result = await service._predict_with_model(mock_model, features, mock_match)

        assert isinstance(result, Prediction)
        assert result.match_id == mock_match.id
        assert result.model_version == mock_model.version
        assert result.predicted_result == MatchResult.HOME_WIN
        assert result.confidence_level == PredictionConfidence.MEDIUM


class TestModelService:
    """Test ModelService class."""

    def test_model_service_initialization(self):
        """Test ModelService initialization."""
        service = ModelService()
        assert service.logger is not None

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_get_available_models_from_cache(self, mock_cache, mock_model):
        """Test getting models from cache."""
        service = ModelService()

        cache_manager = AsyncMock()
        cached_models = [mock_model.dict()]
        cache_manager.get.return_value = cached_models
        mock_cache.return_value = cache_manager

        result = await service.get_available_models()

        assert len(result) == 1
        assert isinstance(result[0], Model)
        cache_manager.get.assert_called_once_with("available_models", "models")

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_get_available_models_from_registry(self, mock_cache, mock_model):
        """Test getting models from registry."""
        service = ModelService()

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True
        mock_cache.return_value = cache_manager

        service._load_models_from_registry = AsyncMock(return_value=[mock_model])

        result = await service.get_available_models()

        assert len(result) == 1
        assert result[0] == mock_model
        cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_model_by_version_found(self, mock_model):
        """Test getting model by version when found."""
        service = ModelService()

        service.get_available_models = AsyncMock(return_value=[mock_model])

        result = await service.get_model_by_version("v1.0.0")

        assert result == mock_model

    @pytest.mark.asyncio
    async def test_get_model_by_version_not_found(self, mock_model):
        """Test getting model by version when not found."""
        service = ModelService()

        service.get_available_models = AsyncMock(return_value=[mock_model])

        result = await service.get_model_by_version("v2.0.0")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_default_model_production(self, mock_model):
        """Test getting default model (production)."""
        service = ModelService()

        # Create production and non-production models
        prod_model = mock_model
        prod_model.is_production = True

        non_prod_model = Model(
            id=uuid4(),
            name="non_prod_model",
            version="v0.9.0",
            type=ModelType.XGBOOST,
            status=ModelStatus.ACTIVE,
            is_production=False,
            is_active=True
        )

        service.get_available_models = AsyncMock(
            return_value=[non_prod_model, prod_model]
        )

        result = await service.get_default_model()

        assert result == prod_model

    @pytest.mark.asyncio
    async def test_get_default_model_active_fallback(self, mock_model):
        """Test getting default model fallback to active."""
        service = ModelService()

        # Create only active models, no production
        active_model = mock_model
        active_model.is_production = False
        active_model.is_active = True

        service.get_available_models = AsyncMock(return_value=[active_model])

        result = await service.get_default_model()

        assert result == active_model

    @pytest.mark.asyncio
    async def test_get_default_model_none_available(self):
        """Test getting default model when none available."""
        service = ModelService()

        service.get_available_models = AsyncMock(return_value=[])

        result = await service.get_default_model()

        assert result is None

    @pytest.mark.asyncio
    async def test_load_models_from_registry_placeholder(self):
        """Test _load_models_from_registry placeholder method."""
        service = ModelService()
        result = await service._load_models_from_registry()
        assert result == []


class TestDataService:
    """Test DataService class."""

    def test_data_service_initialization(self):
        """Test DataService initialization."""
        service = DataService()
        assert service.logger is not None

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_get_match_data_from_cache(self, mock_cache, mock_match):
        """Test getting match data from cache."""
        service = DataService()

        cache_manager = AsyncMock()
        cache_manager.get.return_value = mock_match.dict()
        mock_cache.return_value = cache_manager

        result = await service.get_match_data(mock_match.id)

        assert isinstance(result, Match)
        cache_manager.get.assert_called_once()

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_get_match_data_from_db(self, mock_cache, mock_match):
        """Test getting match data from database."""
        service = DataService()

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True
        mock_cache.return_value = cache_manager

        service._load_match_from_db = AsyncMock(return_value=mock_match)

        result = await service.get_match_data(mock_match.id)

        assert result == mock_match
        cache_manager.set.assert_called_once()

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_get_team_data_from_cache(self, mock_cache, mock_team):
        """Test getting team data from cache."""
        service = DataService()

        cache_manager = AsyncMock()
        cache_manager.get.return_value = mock_team.dict()
        mock_cache.return_value = cache_manager

        result = await service.get_team_data(mock_team.id)

        assert isinstance(result, Team)
        cache_manager.get.assert_called_once()

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_get_upcoming_matches_from_cache(self, mock_cache, mock_match):
        """Test getting upcoming matches from cache."""
        service = DataService()

        cache_manager = AsyncMock()
        cache_manager.get.return_value = [mock_match.dict()]
        mock_cache.return_value = cache_manager

        result = await service.get_upcoming_matches(7)

        assert len(result) == 1
        assert isinstance(result[0], Match)
        cache_manager.get.assert_called_once_with("upcoming_7d", "matches")

    @patch('football_predict_system.domain.services.get_cache_manager')
    @pytest.mark.asyncio
    async def test_get_upcoming_matches_from_db(self, mock_cache, mock_match):
        """Test getting upcoming matches from database."""
        service = DataService()

        cache_manager = AsyncMock()
        cache_manager.get.return_value = None
        cache_manager.set.return_value = True
        mock_cache.return_value = cache_manager

        service._load_upcoming_matches_from_db = AsyncMock(
            return_value=[mock_match]
        )

        result = await service.get_upcoming_matches(14)

        assert len(result) == 1
        assert result[0] == mock_match
        cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_match_from_db_placeholder(self):
        """Test _load_match_from_db placeholder method."""
        service = DataService()
        result = await service._load_match_from_db(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_load_team_from_db_placeholder(self):
        """Test _load_team_from_db placeholder method."""
        service = DataService()
        result = await service._load_team_from_db(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_load_upcoming_matches_from_db_placeholder(self):
        """Test _load_upcoming_matches_from_db placeholder method."""
        service = DataService()
        end_date = datetime.utcnow() + timedelta(days=7)
        result = await service._load_upcoming_matches_from_db(end_date)
        assert result == []


class TestAnalyticsService:
    """Test AnalyticsService class."""

    def test_analytics_service_initialization(self):
        """Test AnalyticsService initialization."""
        service = AnalyticsService()
        assert service.logger is not None

    @pytest.mark.asyncio
    async def test_get_prediction_accuracy(self):
        """Test prediction accuracy calculation."""
        service = AnalyticsService()

        result = await service.get_prediction_accuracy("v1.0.0", 30)

        assert "accuracy" in result
        assert "total_predictions" in result
        assert "correct_predictions" in result
        assert "period_days" in result
        assert "model_version" in result
        assert result["model_version"] == "v1.0.0"
        assert result["period_days"] == 30
        assert 0 <= result["accuracy"] <= 1

    @pytest.mark.asyncio
    async def test_get_prediction_accuracy_no_model(self):
        """Test prediction accuracy without specific model."""
        service = AnalyticsService()

        result = await service.get_prediction_accuracy(None, 7)

        assert result["model_version"] is None
        assert result["period_days"] == 7

    @pytest.mark.asyncio
    async def test_get_model_performance_comparison(self):
        """Test model performance comparison."""
        service = AnalyticsService()

        result = await service.get_model_performance_comparison()

        assert "models" in result
        assert "comparison_period" in result
        assert "metrics" in result
        assert isinstance(result["models"], list)
        assert result["comparison_period"] == "30_days"
        assert "accuracy" in result["metrics"]


class TestGlobalServiceInstances:
    """Test global service instances."""

    def test_prediction_service_instance(self):
        """Test global prediction service instance."""
        assert isinstance(prediction_service, PredictionService)

    def test_model_service_instance(self):
        """Test global model service instance."""
        assert isinstance(model_service, ModelService)

    def test_data_service_instance(self):
        """Test global data service instance."""
        assert isinstance(data_service, DataService)

    def test_analytics_service_instance(self):
        """Test global analytics service instance."""
        assert isinstance(analytics_service, AnalyticsService)

    def test_service_instances_are_singletons(self):
        """Test that service instances behave like singletons."""
        # Import again to check if same instances
        from football_predict_system.domain.services import analytics_service as as1
        from football_predict_system.domain.services import analytics_service as as2
        from football_predict_system.domain.services import data_service as ds1
        from football_predict_system.domain.services import data_service as ds2
        from football_predict_system.domain.services import model_service as ms1
        from football_predict_system.domain.services import model_service as ms2
        from football_predict_system.domain.services import prediction_service as ps1
        from football_predict_system.domain.services import prediction_service as ps2

        assert ps1 is ps2
        assert ms1 is ms2
        assert ds1 is ds2
        assert as1 is as2
