"""Weather Data Service Interface and Unavailable Fallback implementation."""
from typing import Optional
from backend.app.services.base import BaseWeatherService, WeatherDataResult


class UnavailableWeatherService(BaseWeatherService):
    """Default weather service before Builder 2's ingestion pipeline is active."""

    def __init__(self, data_version: Optional[str] = None):
        self.data_version = data_version

    def fetch_forecast_data(
        self, location: str, target_date: Optional[str] = None
    ) -> WeatherDataResult:
        """Return empty/unavailable data container safely."""
        return WeatherDataResult(
            location=location,
            target_date=target_date,
            raw_data={},
            data_version=self.data_version,
            is_available=False,
            metadata={"status": "PIPELINE_NOT_READY"},
        )
