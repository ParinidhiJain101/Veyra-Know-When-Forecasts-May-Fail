"""Safety, OOD, and Abstention Layer."""
from dataclasses import dataclass
from typing import Optional
from backend.app.schemas.prediction import ReasonCode, RiskLevel, TrustState
from backend.app.services.base import FeatureResult, ModelResult, WeatherDataResult


@dataclass
class SafetyAssessment:
    """Safety evaluation output controlling final trust state and abstention."""

    bust_probability: Optional[float]
    risk_level: Optional[RiskLevel]
    trust_state: TrustState
    abstain: bool
    reason_codes: list[str]


class SafetyEvaluator:
    """Evaluates data validity, ML model availability, and OOD signals to decide on abstention."""

    @staticmethod
    def evaluate(
        weather_result: WeatherDataResult,
        feature_result: FeatureResult,
        model_result: ModelResult,
    ) -> SafetyAssessment:
        """Perform safety evaluation.

        If the model or data pipeline is not ready, safely ABSTAIN with
        trust_state=UNAVAILABLE, bust_probability=None, and MODEL_NOT_READY reason.
        """
        # Case 1: Model is unavailable or probability is null
        if not model_result.is_ready or model_result.probability is None:
            return SafetyAssessment(
                bust_probability=None,
                risk_level=None,
                trust_state=TrustState.UNAVAILABLE,
                abstain=True,
                reason_codes=[ReasonCode.MODEL_NOT_READY.value],
            )

        # Future pipeline safety checks (when Builder 2 model is plugged in)
        probability = model_result.probability

        # Determine risk level based on calibrated probability
        risk_level = SafetyEvaluator._map_risk_level(probability)

        # Default confident prediction (future OOD evaluation will plug in here)
        return SafetyAssessment(
            bust_probability=probability,
            risk_level=risk_level,
            trust_state=TrustState.HIGH_CONFIDENCE,
            abstain=False,
            reason_codes=[ReasonCode.SUCCESS.value],
        )

    @staticmethod
    def _map_risk_level(prob: float) -> RiskLevel:
        """Map a calibrated probability to a categorical risk level."""
        if prob < 0.20:
            return RiskLevel.LOW
        elif prob < 0.50:
            return RiskLevel.MEDIUM
        elif prob < 0.75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
