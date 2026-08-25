"""Feature Engineering Service Interface and Fallback implementation."""
from backend.app.schemas.prediction import ReasonCode
from backend.app.services.base import BaseFeatureService, FeatureResult, WeatherResult


class UnavailableFeatureService(BaseFeatureService):
    """Default fallback feature service before Builder 2's feature pipeline is integrated.

    Always returns an explicit unavailable state safely without fabricating fake features.
    """

    def build_features(self, weather_result: WeatherResult) -> FeatureResult:
        """Return empty feature vector safely."""
        return FeatureResult(
            location=weather_result.location,
            features={},
            feature_names=[],
            is_ready=False,
            metadata={"status": ReasonCode.FEATURES_NOT_READY.value},
            error="Feature engineering pipeline is not yet integrated",
        )
