"""Feature Engineering Service Interface and Fallback implementation."""
from backend.app.services.base import (
    BaseFeatureService,
    FeatureResult,
    WeatherDataResult,
)


class UnavailableFeatureService(BaseFeatureService):
    """Default feature engineering service before Builder 2's feature pipeline is active."""

    def extract_features(self, weather_data: WeatherDataResult) -> FeatureResult:
        """Return empty feature vector safely."""
        return FeatureResult(
            location=weather_data.location,
            features={},
            is_ready=False,
            metadata={"status": "FEATURE_PIPELINE_NOT_READY"},
        )
