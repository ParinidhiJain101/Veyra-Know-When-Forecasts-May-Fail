"""
Operational Forecast-Risk Engine (Day 6).

Coordinates location colocation, issue-time feature extraction, calibrated model
inference via ForecastBustModelService, dynamic verification status derivation,
and structured explanation generation.

SCIENTIFIC CONSTRAINTS:
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
    DataStatus,
    ForecastRiskItem,
    ForecastRiskResponse,
    LocationInfo,
    ProvenanceInfo,
    VerificationStatus,
)
from features.feature_pipeline import FEATURE_COLUMN_NAMES, IssueTimeSafeFeaturePipeline
from models.model_service import ForecastBustModelService


class OperationalRiskEngine:
    """Operational engine turning weather forecasts into calibrated bust risk products."""

    def __init__(
        self,
        model_service: Optional[ForecastBustModelService] = None,
        location_registry: Optional[LocationRegistry] = None,
        feature_pipeline: Optional[IssueTimeSafeFeaturePipeline] = None,
    ):
        self.model_service = model_service or ForecastBustModelService()
        self.location_registry = location_registry or LocationRegistry()
        self.feature_pipeline = feature_pipeline or IssueTimeSafeFeaturePipeline()

    def evaluate_verification_status(
        self,
        valid_time: datetime,
        issue_time: datetime,
        max_truth_time_utc: Optional[datetime] = None,
        has_verified_truth_pair: bool = False,
    ) -> str:
        """
        Derive ground-truth verification status from actual temporal and truth availability context.

        SCIENTIFIC INTEGRITY RULES:
        1. An actual verified observation pair MUST be present to return HISTORICALLY_VERIFIED.
        2. If valid_time exceeds an explicit truth archive cutoff, returns UNVERIFIED_HORIZON_NO_TRUTH.
        3. If valid_time is in the future relative to the clock, returns NO_TRUTH_AVAILABLE.
        4. If a pair is absent even within the archive window, returns NO_TRUTH_AVAILABLE.

        Args:
            valid_time: Forecast target time (UTC).
            issue_time: Forecast cycle initialization time (UTC).
            max_truth_time_utc: Latest timestamp for which ground truth reanalysis is available.
            has_verified_truth_pair: True if a verified observation pair exists in the dataset.

        Returns:
            VerificationStatus string value.
        """
        # Rule 1: Verified pair takes precedence
        if has_verified_truth_pair:
            return VerificationStatus.HISTORICALLY_VERIFIED.value

        # Rule 2: Past the explicit truth archive window
        if max_truth_time_utc is not None and valid_time > max_truth_time_utc:
            return VerificationStatus.UNVERIFIED_HORIZON_NO_TRUTH.value

        # Rule 3: Future forecast target relative to real-time clock
        now_utc = datetime.now(timezone.utc)
        if valid_time > now_utc:
            return VerificationStatus.NO_TRUTH_AVAILABLE.value

        # Rule 4: Covered by time window or past, but observation pair is absent
        return VerificationStatus.NO_TRUTH_AVAILABLE.value

    def resolve_grid_resolution(
        self,
        explicit_res: Optional[str] = None,
        df_forecast: Optional[pd.DataFrame] = None,
        forecast_source: Optional[str] = None,
    ) -> str:
        """
        Derive grid resolution provenance without silent guesswork.

        Returns:
            Grid resolution string (e.g. '0.25°', '0.50°') or 'UNKNOWN'.
        """
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
        Execute full operational risk pipeline for a standardized forecast DataFrame.

        Args:
            df_forecast: Standardized forecast DataFrame containing forecast values and ensemble stats.
            location_id: Identifier of the target location.
            forecast_source: Name of NWP forecast provider.
            grid_resolution: Optional grid resolution string.
            max_truth_time_utc: Optional cutoff timestamp for available ground truth verification.

        Returns:
            ForecastRiskResponse dataclass.
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

        # 4. Extract Features strictly using existing Builder 2 Feature Pipeline
        if all(c in df_forecast.columns for c in FEATURE_COLUMN_NAMES):
            X = df_forecast[FEATURE_COLUMN_NAMES].copy()
            meta_df = df_forecast.copy()
        else:
            X, meta_df = self.feature_pipeline.extract_features(df_forecast)

        # 5. Invoke Model Service for Batch Inference
        predictions = self.model_service.predict(X)

        # 6. Extract metadata & provenance
        model_meta = self.model_service.get_metadata()
        model_version = model_meta.get("model_version", "prototype-gbm-v1")
        decision_threshold = float(model_meta.get("decision_threshold", 0.280))

        issue_time_val = meta_df["issue_time"].iloc[0] if "issue_time" in meta_df.columns else datetime.now(timezone.utc)
        issue_time_str = pd.to_datetime(issue_time_val, utc=True).isoformat()

        provenance = ProvenanceInfo(
            forecast_source=forecast_source,
            grid_resolution=resolved_grid_res,
            model_version=model_version,
            feature_schema_version=model_meta.get("feature_schema_version", "1.0.0"),
            prediction_timestamp_utc=datetime.now(timezone.utc).isoformat(),
            truth_source="ECMWF_ERA5_REANALYSIS",
        )

        # 7. Assemble Forecast Risk Items
        forecast_items: List[ForecastRiskItem] = []

        for idx, (p_res, (_, row_meta), (_, row_feat)) in enumerate(zip(predictions, meta_df.iterrows(), X.iterrows())):
            prob = float(p_res["probability"])
            alert = bool(p_res["bust_alert"])

            v_time_dt = pd.to_datetime(row_meta.get("valid_time", issue_time_val), utc=True).to_pydatetime()
            i_time_dt = pd.to_datetime(row_meta.get("issue_time", issue_time_val), utc=True).to_pydatetime()

            lead_h = int(row_feat["lead_hours"])
            lead_d = float(row_feat["lead_days"])
            var_name = str(row_meta.get("variable", "temperature_2m"))

            # Determine verification status dynamically
            has_truth = "forecast_abs_error" in row_meta and not pd.isna(row_meta["forecast_abs_error"])
            v_status = self.evaluate_verification_status(
                valid_time=v_time_dt,
                issue_time=i_time_dt,
                max_truth_time_utc=max_truth_time_utc,
                has_verified_truth_pair=has_truth,
            )

            # Generate physical explanation
            explanation = ForecastBustExplainer.explain_row(
                feature_row=row_feat.to_dict(),
                bust_probability=prob,
                threshold=decision_threshold,
            )

            # Extract forecast values safely
            f_val = float(row_feat.get("forecast_value", row_meta.get("value", 0.0)))
            ens_mean = float(row_feat.get("ensemble_mean", f_val))
            ens_std = float(row_feat.get("ensemble_std", 0.0))
            unit = str(row_meta.get("unit", "degC" if "temperature" in var_name else ("hPa" if "pressure" in var_name else "km/h")))

            forecast_items.append(
                ForecastRiskItem(
                    valid_time=v_time_dt.isoformat(),
                    lead_hours=lead_h,
                    lead_days=lead_d,
                    variable=var_name,
                    forecast_value=f_val,
                    ensemble_mean=ens_mean,
                    ensemble_std=ens_std,
                    unit=unit,
                    bust_probability=prob,
                    bust_alert=alert,
                    data_status=DataStatus.MODEL_PREDICTION.value,
                    verification_status=v_status,
                    explanation=explanation,
                    confidence=None,  # Omitted until real OOD/calibration confidence layer is implemented
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
