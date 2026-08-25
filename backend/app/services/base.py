"""Abstract Base Service Interfaces for Forecast-Bust Sentinel."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class WeatherDataResult:
    """Standard container for fetched weather forecast and observation data."""

    location: str
    target_date: Optional[str] = None
    raw_data: dict[str, Any] = field(default_factory=dict)
    data_version: Optional[str] = None
    is_available: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureResult:
    """Standard container for engineered ML features."""

    location: str
    features: dict[str, float] = field(default_factory=dict)
    is_ready: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResult:
    """Standard container for ML model prediction output."""

    probability: Optional[float] = None
    model_version: Optional[str] = None
    is_ready: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseWeatherService(ABC):
    """Interface for Weather Data Collection services (Builder 2 integration hook)."""

    @abstractmethod
    def fetch_forecast_data(
        self, location: str, target_date: Optional[str] = None
    ) -> WeatherDataResult:
        """Fetch raw forecast and atmospheric data for a given location."""
        pass


class BaseFeatureService(ABC):
    """Interface for Feature Engineering services (Builder 2 integration hook)."""

    @abstractmethod
    def extract_features(self, weather_data: WeatherDataResult) -> FeatureResult:
        """Transform raw forecast data into engineered feature vectors."""
        pass


class BaseModelService(ABC):
    """Interface for ML Bust Probability Estimation models (Builder 2 integration hook)."""

    @abstractmethod
    def predict(self, feature_result: FeatureResult) -> ModelResult:
        """Generate calibrated forecast-bust probability given engineered features."""
        pass
