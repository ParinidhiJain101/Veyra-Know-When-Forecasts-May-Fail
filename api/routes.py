"""
API Router and Service Handlers (Day 6).

Provides typed dispatching functions for health checks, location listings,
forecast risk inference, and regional risk aggregations.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from api.location_service import LocationRegistry
from api.regional_aggregator import RegionalRiskAggregator
from api.risk_engine import OperationalRiskEngine
from api.schemas import (
    ForecastRiskResponse,
    RegionalRiskSummaryResponse,
)


class ForecastBustAPI:
    """REST API service controller for Forecast-Bust Sentinel."""

    def __init__(
        self,
        risk_engine: Optional[OperationalRiskEngine] = None,
        location_registry: Optional[LocationRegistry] = None,
    ):
        self.risk_engine = risk_engine or OperationalRiskEngine()
        self.location_registry = location_registry or LocationRegistry()

    def get_health(self) -> Dict[str, Any]:
        """Return system health, loaded model version, and runtime status."""
        model_meta = self.risk_engine.model_service.get_metadata()
        return {
            "status": "healthy",
            "service": "Forecast-Bust Sentinel Operational API",
            "model_version": model_meta.get("model_version", "prototype-gbm-v1"),
            "decision_threshold": model_meta.get("decision_threshold", 0.280),
            "feature_count": model_meta.get("feature_count", 26),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }

    def list_locations(self) -> Dict[str, Any]:
        """Return all registered meteorological monitoring locations."""
        locations = self.location_registry.list_locations()
        return {
            "count": len(locations),
            "locations": locations,
        }

    def get_forecast_risk(
        self,
        forecast_input: Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]],
        location_id: str = "delhi",
        forecast_source: str = "NOAA_GEFS",
        grid_resolution: Optional[str] = None,
        max_truth_time_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Compute operational forecast bust probabilities and explanations.

        Args:
            forecast_input: DataFrame or records of standardized forecast steps.
            location_id: Target location ID.
            forecast_source: NWP forecast source name.
            grid_resolution: Optional grid resolution string.
            max_truth_time_utc: Optional ground-truth cutoff timestamp for verification status.

        Returns:
            Dict representing ForecastRiskResponse.
        """
        if isinstance(forecast_input, pd.DataFrame):
            df = forecast_input
        elif isinstance(forecast_input, list):
            df = pd.DataFrame(forecast_input)
        elif isinstance(forecast_input, dict):
            df = pd.DataFrame([forecast_input])
        else:
            raise TypeError(f"Unsupported forecast_input type: {type(forecast_input).__name__}")

        response: ForecastRiskResponse = self.risk_engine.process_forecast_dataframe(
            df_forecast=df,
            location_id=location_id,
            forecast_source=forecast_source,
            grid_resolution=grid_resolution,
            max_truth_time_utc=max_truth_time_utc,
        )

        return response.to_dict()

    def get_regional_summary(
        self,
        region_name: str,
        location_forecast_inputs: Dict[str, Union[pd.DataFrame, List[Dict[str, Any]]]],
        forecast_source: str = "NOAA_GEFS",
        grid_resolution: Optional[str] = None,
        max_truth_time_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Compute transparent spatial summary across multiple locations in a region.

        Args:
            region_name: Descriptive region name.
            location_forecast_inputs: Dict mapping location_id -> forecast data.
            forecast_source: NWP forecast source name.
            grid_resolution: Optional grid resolution string.
            max_truth_time_utc: Optional ground-truth cutoff timestamp.

        Returns:
            Dict representing RegionalRiskSummaryResponse.
        """
        responses: List[ForecastRiskResponse] = []

        for loc_id, f_data in location_forecast_inputs.items():
            if isinstance(f_data, pd.DataFrame):
                df = f_data
            else:
                df = pd.DataFrame(f_data)

            resp = self.risk_engine.process_forecast_dataframe(
                df_forecast=df,
                location_id=loc_id,
                forecast_source=forecast_source,
                grid_resolution=grid_resolution,
                max_truth_time_utc=max_truth_time_utc,
            )
            responses.append(resp)

        summary: RegionalRiskSummaryResponse = RegionalRiskAggregator.aggregate_region(
            region_name=region_name,
            location_responses=responses,
        )

        return summary.to_dict()
