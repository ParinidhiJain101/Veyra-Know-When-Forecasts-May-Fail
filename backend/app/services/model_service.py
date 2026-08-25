"""Model Service Interface and Unavailable Fallback implementation."""
from typing import Optional
from backend.app.services.base import BaseModelService, FeatureResult, ModelResult


class UnavailableModelService(BaseModelService):
    """Default model service when Builder 2's trained ML model is not yet integrated."""

    def __init__(self, model_version: Optional[str] = None):
        self.model_version = model_version

    def predict(self, feature_result: FeatureResult) -> ModelResult:
        """Return explicit unavailable state without faking any probabilities.

        CRITICAL: bust_probability MUST remain None (null) until a real
        calibrated model is plugged in. Never invent or fake probabilities.
        """
        return ModelResult(
            probability=None,
            model_version=self.model_version,
            is_ready=False,
            metadata={"status": "MODEL_NOT_READY"},
        )
