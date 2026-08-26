"""Forecast bust prediction endpoint with live model serving."""
from fastapi import APIRouter, Depends
from backend.app.agents.forecast_bust_agent import ForecastBustAgent
from backend.app.safety.abstention import SafetyEvaluator
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.services.feature_service import LiveFeatureService
from backend.app.services.model_service import LiveLogisticModelService
from backend.app.services.openmeteo_service import OpenMeteoGEFSWeatherService

router = APIRouter()

# Default live production agent with real weather, feature, and model services
_default_agent = ForecastBustAgent(
    weather_service=OpenMeteoGEFSWeatherService(),
    feature_service=LiveFeatureService(),
    model_service=LiveLogisticModelService(),
    safety_evaluator=SafetyEvaluator(),
)


def get_forecast_bust_agent() -> ForecastBustAgent:
    """Dependency provider for ForecastBustAgent."""
    return _default_agent


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict Forecast Bust Risk",
    description=(
        "Evaluates the probability and risk of an issued weather forecast failing unusually badly "
        "using real-time GEFS weather ingestion, leakage-safe feature engineering, and the trained baseline ML model."
    ),
)
async def predict_forecast_bust(
    request: PredictionRequest,
    agent: ForecastBustAgent = Depends(get_forecast_bust_agent),
) -> PredictionResponse:
    """Evaluate forecast bust probability."""
    return agent.analyze(request)
