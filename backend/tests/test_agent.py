"""Unit tests for ForecastBustAgent orchestrator."""
from backend.app.agents.forecast_bust_agent import ForecastBustAgent
from backend.app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    ReasonCode,
    RiskLevel,
    TrustState,
)
from backend.app.services.base import (
    BaseModelService,
    FeatureResult,
    ModelResult,
)


def test_agent_unavailable_state_default():
    """Test that default ForecastBustAgent returns safe unavailable state."""
    agent = ForecastBustAgent()
    request = PredictionRequest(location="London")
    response = agent.analyze(request)

    assert isinstance(response, PredictionResponse)
    assert response.location == "London"
    assert response.bust_probability is None
    assert response.risk_level is None
    assert response.trust_state == TrustState.UNAVAILABLE
    assert response.abstain is True
    assert ReasonCode.MODEL_NOT_READY.value in response.reason_codes
    assert response.model_version is None
    assert response.data_version is None


def test_agent_future_builder2_model_injection_contract():
    """Test that ForecastBustAgent properly handles a future Builder-2 calibrated model service."""

    class MockBuilder2ModelService(BaseModelService):
        """Simulates Builder 2's calibrated model service."""

        def predict(self, feature_result: FeatureResult) -> ModelResult:
            return ModelResult(
                probability=0.35,
                model_version="prototype-gbm-v1",
                is_ready=True,
                metadata={"calibration": "isotonic"},
            )

    agent = ForecastBustAgent(model_service=MockBuilder2ModelService())
    request = PredictionRequest(location="Tokyo")
    response = agent.analyze(request)

    assert response.location == "Tokyo"
    assert response.bust_probability == 0.35
    assert response.risk_level == RiskLevel.MEDIUM
    assert response.trust_state == TrustState.HIGH_CONFIDENCE
    assert response.abstain is False
    assert response.model_version == "prototype-gbm-v1"
    assert ReasonCode.SUCCESS.value in response.reason_codes
