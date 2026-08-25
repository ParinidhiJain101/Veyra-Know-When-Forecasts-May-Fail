"""Services package exporting base interfaces and default implementations."""
from backend.app.services.base import (
    BaseFeatureService,
    BaseModelService,
    BaseSafetyService,
    BaseWeatherService,
    FeatureResult,
    ModelResult,
    WeatherDataResult,
    WeatherResult,
)
from backend.app.services.feature_service import UnavailableFeatureService
from backend.app.services.model_service import UnavailableModelService
from backend.app.services.weather_service import UnavailableWeatherService

__all__ = [
    "BaseWeatherService",
    "BaseFeatureService",
    "BaseModelService",
    "BaseSafetyService",
    "WeatherResult",
    "WeatherDataResult",
    "FeatureResult",
    "ModelResult",
    "UnavailableWeatherService",
    "UnavailableFeatureService",
    "UnavailableModelService",
]
