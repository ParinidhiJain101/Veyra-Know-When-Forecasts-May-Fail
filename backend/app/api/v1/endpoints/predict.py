"""Forecast bust prediction endpoint with live model serving."""
import os
from fastapi import APIRouter, Depends
from backend.app.agents.forecast_bust_agent import ForecastBustAgent
from backend.app.builder2.feature_adapter import Builder2FeatureAdapter
from backend.app.builder2.model_adapter import Builder2ModelAdapter
from backend.app.core.config import settings
from backend.app.safety.abstention import SafetyEvaluator
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.services.openmeteo_service import OpenMeteoGEFSWeatherService

router = APIRouter()


def create_forecast_bust_agent() -> ForecastBustAgent:
    """Factory creating ForecastBustAgent backed by Builder 2 V2 HTTP Service.

    Routes all forecast-bust risk evaluations to the authoritative Builder 2 V2 engine.
    Never falls back to legacy prototype models.
    """
    target_url = os.getenv("BUILDER2_API_URL") or getattr(settings, "BUILDER2_API_URL", None) or os.getenv("BUILDER2_URL", "http://localhost:8001")
    return ForecastBustAgent(
        weather_service=OpenMeteoGEFSWeatherService(),
        feature_service=Builder2FeatureAdapter(),
        model_service=Builder2ModelAdapter(api_url=target_url, timeout_seconds=2.0),
        safety_evaluator=SafetyEvaluator(),
    )


def get_forecast_bust_agent() -> ForecastBustAgent:
    """Dependency provider for ForecastBustAgent."""
    return create_forecast_bust_agent()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict Forecast Bust Risk",
    description=(
        "Evaluates the probability and risk of an issued weather forecast failing unusually badly "
        "using Builder 2 V2 LightGBM model with Platt Sigmoid calibration."
    ),
)
def predict_forecast_bust(
    request: PredictionRequest,
    agent: ForecastBustAgent = Depends(get_forecast_bust_agent),
) -> PredictionResponse:
    """Execute live forecast bust risk assessment."""
    return agent.analyze(request)
