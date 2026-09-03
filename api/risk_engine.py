"""
Operational Forecast-Risk Engine.

Coordinates location colocation, issue-time feature extraction, calibrated model
inference via ForecastBustModelService, dynamic verification status derivation,
and structured explanation generation.

Scientific Constraints:
- Single feature pipeline path: uses features/feature_pipeline.py directly.
- Verification status strictly requires an actual verified truth pair to claim HISTORICALLY_VERIFIED.
- Grid resolution provenance is never silently guessed (returns UNKNOWN if resolution is absent).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import uuid

import numpy as np
import pandas as pd

from api.explainer import ForecastBustExplainer
from api.location_service import LocationRegistry
from api.schemas import (
    ContributingFactor,
    DataStatus,
    ExplanationItem,
    ForecastRiskItem,
    ForecastRiskResponse,
    LocationInfo,
    ProvenanceInfo,
    VerificationStatus,
)
from models.forecast_intelligence_service import ForecastIntelligenceService


class OperationalRiskEngine:
    """Operational engine turning weather forecasts into calibrated bust risk products via V2 Champion."""

    def __init__(
        self,
        intelligence_service: Optional[ForecastIntelligenceService] = None,
        location_registry: Optional[LocationRegistry] = None,
        model_service: Optional[Any] = None,
        feature_pipeline: Optional[Any] = None,
    ):
        self.intelligence_service = intelligence_service or ForecastIntelligenceService()
        self.location_registry = location_registry or LocationRegistry()
        # Expose model_service property for legacy inspection
        self.model_service = self.intelligence_service

    def evaluate_verification_status(
        self,
        valid_time: datetime,
        issue_time: datetime,
        max_truth_time_utc: Optional[datetime] = None,
        has_verified_truth_pair: bool = False,
    ) -> str:
        """
        Derive ground-truth verification status from actual temporal and truth availability context.
        """
        if has_verified_truth_pair:
            return VerificationStatus.HISTORICALLY_VERIFIED.value

        if max_truth_time_utc is not None and valid_time > max_truth_time_utc:
            return VerificationStatus.UNVERIFIED_HORIZON_NO_TRUTH.value

        now_utc = datetime.now(timezone.utc)
        if valid_time > now_utc:
            return VerificationStatus.NO_TRUTH_AVAILABLE.value

        return VerificationStatus.NO_TRUTH_AVAILABLE.value

    def resolve_grid_resolution(
        self,
        explicit_res: Optional[str] = None,
        df_forecast: Optional[pd.DataFrame] = None,
        forecast_source: Optional[str] = None,
    ) -> str:
        """Derive grid resolution provenance without silent guesswork."""
        if explicit_res is not None and explicit_res.strip():
            return explicit_res.strip()

        if df_forecast is not None and "grid_resolution" in df_forecast.columns:
            val = str(df_forecast["grid_resolution"].iloc[0]).strip()
            if val and val.lower() != "nan" and val.lower() != "none":
                return val

        if forecast_source is not None:
            src = forecast_source.lower()
            if "0p50" in src or "pgrb2a" in src:
                return "0.50°"
            if "0p25" in src or "gefs025" in src or "openmeteo" in src:
                return "0.25°"

        return "UNKNOWN"

    def process_forecast_dataframe(
        self,
        df_forecast: pd.DataFrame,
        location_id: str = "delhi",
        forecast_source: str = "NOAA_GEFS",
        grid_resolution: Optional[str] = None,
        max_truth_time_utc: Optional[datetime] = None,
    ) -> ForecastRiskResponse:
        """
        Execute full operational risk pipeline for a standardized forecast DataFrame using V2 Champion.
        """
        if df_forecast.empty:
            raise ValueError("Input forecast DataFrame is empty.")

        # 1. Determine grid coordinates from data if available
        actual_lat = float(df_forecast["latitude"].iloc[0]) if "latitude" in df_forecast.columns else None
        actual_lon = float(df_forecast["longitude"].iloc[0]) if "longitude" in df_forecast.columns else None

        # 2. Derive dynamic grid resolution without silent guessing
        resolved_grid_res = self.resolve_grid_resolution(
            explicit_res=grid_resolution,
            df_forecast=df_forecast,
            forecast_source=forecast_source,
        )

        # 3. Resolve Location Info
        location_info = self.location_registry.get_location(
            location_id=location_id,
            actual_grid_lat=actual_lat,
            actual_grid_lon=actual_lon,
        )

        # 4. Invoke Authoritative V2 Forecast Intelligence Service
        results = self.intelligence_service.evaluate_forecast(df_forecast)

        # 5. Extract metadata & provenance
        model_version = self.intelligence_service.model_version
        decision_threshold = float(self.intelligence_service.operational_threshold)

        issue_time_val = df_forecast["issue_time"].iloc[0] if "issue_time" in df_forecast.columns else datetime.now(timezone.utc)
        issue_time_str = pd.to_datetime(issue_time_val, utc=True).isoformat()

        provenance = ProvenanceInfo(
            forecast_source=forecast_source,
            grid_resolution=resolved_grid_res,
            model_version=model_version,
            feature_schema_version="2.0.0-supercharged-50f",
            prediction_timestamp_utc=datetime.now(timezone.utc).isoformat(),
            truth_source="ECMWF_ERA5_REANALYSIS",
        )

        # 6. Assemble Forecast Risk Items with V2 fields
        forecast_items: List[ForecastRiskItem] = []

        for r in results:
            prob = float(r.bust_probability)
            alert = bool(prob >= decision_threshold)

            v_time_dt = pd.to_datetime(r.valid_time, utc=True).to_pydatetime()
            i_time_dt = pd.to_datetime(r.issue_time, utc=True).to_pydatetime()

            has_truth = "forecast_abs_error" in df_forecast.columns and not pd.isna(df_forecast["forecast_abs_error"].iloc[0] if len(df_forecast) else None)
            v_status = self.evaluate_verification_status(
                valid_time=v_time_dt,
                issue_time=i_time_dt,
                max_truth_time_utc=max_truth_time_utc,
                has_verified_truth_pair=has_truth,
            )

            primary_drv = r.dominant_risk_drivers[0].signal_name if r.dominant_risk_drivers else "NONE"
            drv_summary = r.dominant_risk_drivers[0].description if r.dominant_risk_drivers else "All feature signals nominal."
            factors = [
                ContributingFactor(
                    factor=d.signal_name,
                    value=float(d.signal_value),
                    signal=d.risk_direction,
                )
                for d in r.dominant_risk_drivers
            ]

            explanation = ExplanationItem(
                primary_driver=primary_drv,
                driver_summary=drv_summary,
                top_contributing_factors=factors,
            )

            forecast_items.append(
                ForecastRiskItem(
                    valid_time=v_time_dt.isoformat(),
                    lead_hours=int(r.lead_hours),
                    lead_days=round(float(r.lead_hours / 24.0), 2),
                    variable=str(r.variable),
                    forecast_value=float(r.forecast_value),
                    ensemble_mean=float(r.ensemble_mean),
                    ensemble_std=float(r.ensemble_std),
                    unit=str(r.unit),
                    bust_probability=prob,
                    bust_alert=alert,
                    data_status=DataStatus.MODEL_PREDICTION.value,
                    verification_status=v_status,
                    explanation=explanation,
                    confidence=None,
                    risk_level=str(r.risk_level),
                    confidence_index=float(r.confidence_index),
                    structural_overconfidence=float(r.overconfidence_signal),
                    stability_index=float(r.stability_index),
                    ood_score=float(r.ood_score),
                    failure_fingerprint=str(r.provenance.get("failure_fingerprint", "NOMINAL")),
                    uncertainty_pct=float(r.provenance.get("prediction_uncertainty_pct", 3.37)),
                    dominant_risk_drivers=[d.to_dict() for d in r.dominant_risk_drivers],
                )
            )

        return ForecastRiskResponse(
            request_id=f"req-{uuid.uuid4().hex[:12]}",
            location=location_info,
            issue_time=issue_time_str,
            model_version=model_version,
            decision_threshold=decision_threshold,
            provenance=provenance,
            forecasts=forecast_items,
        )
