"""Services package exporting base interfaces and default implementations."""
from backend.app.services.base import (
    BaseFeatureService,
    BaseModelService,
    BaseWeatherService,
    FeatureResult,
    ModelResult,
    WeatherDataResult,
)
from backend.app.services.feature_service import UnavailableFeatureService
from backend.app.services.model_service import UnavailableModelService
from backend.app.services.weather_service import UnavailableWeatherService

__all__ = [
    "BaseWeatherService",
    "BaseFeatureService",
    "BaseModelService",
    "WeatherDataResult",
    "FeatureResult",
    "ModelResult",
    "UnavailableWeatherService",
    "UnavailableFeatureService",
    "UnavailableModelService",
]
