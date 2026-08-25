"""Forecast bust prediction endpoint."""
from fastapi import APIRouter, Depends
from backend.app.agents.forecast_bust_agent import ForecastBustAgent
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter()

# Default singleton instance for the agent
_default_agent = ForecastBustAgent()


def get_forecast_bust_agent() -> ForecastBustAgent:
    """Dependency provider for ForecastBustAgent."""
    return _default_agent


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict Forecast Bust",
    description=(
        "Evaluates the probability and risk of an issued weather forecast failing unusually badly. "
        "Returns a safe ABSTAIN state with trust_state=UNAVAILABLE while the ML model is not ready."
    ),
)
async def predict_forecast_bust(
    request: PredictionRequest,
    agent: ForecastBustAgent = Depends(get_forecast_bust_agent),
) -> PredictionResponse:
    """Evaluate forecast bust probability."""
    return agent.analyze(request)
