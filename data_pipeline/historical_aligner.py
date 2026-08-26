"""
Historical Alignment & Forecast Error Engine.

Aligns standardized GEFS forecast predictions with ECMWF ERA5 reanalysis ground truth
by location, variable, and valid_time under an explicit spatial colocation policy.

Calculates:
- Signed forecast error: error = forecast_value - truth_value
- Absolute forecast error: abs_error = |forecast_value - truth_value|
- Ensemble mean signed error: ens_mean_error = ensemble_mean - truth_value
- Ensemble mean absolute error: ens_mean_abs_error = |ensemble_mean - truth_value|
- Spatial colocation distance (km)

Scientific Safeguard:
Truth observations and error metrics are strictly for verification, historical training,
and evaluation. They are never live forecast features.
"""

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


PAIRED_DATASET_COLUMNS = [
    "location",
    "latitude",
    "longitude",
    "issue_time",
    "valid_time",
    "lead_hours",
    "variable",
    "forecast_value",
    "forecast_unit",
    "forecast_source",
    "ensemble_mean",
    "ensemble_std",
    "ensemble_min",
    "ensemble_max",
    "q10",
    "q90",
    "member_count",
    "truth_value",
    "truth_unit",
    "truth_source",
    "forecast_error",
    "forecast_abs_error",
    "ensemble_mean_error",
    "ensemble_mean_abs_error",
    "spatial_distance_km",
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two coordinates in kilometers."""
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 3)


def standardize_era5_reference(
    raw_era5: Dict[str, Any],
    location_name: str = "delhi",
    truth_source: str = "ERA5_REANALYSIS",
) -> pd.DataFrame:
    """
    Standardize raw ERA5 historical JSON into structured reference DataFrame.

    Args:
        raw_era5: Raw JSON from ERA5ReferenceCollector.
        location_name: Location identifier.
        truth_source: Identifier for truth source.

    Returns:
        pd.DataFrame with columns: ['location', 'latitude', 'longitude', 'valid_time', 'variable', 'truth_value', 'truth_unit', 'truth_source']
    """
    hourly = raw_era5.get("hourly", {})
    if not hourly or "time" not in hourly:
        raise ValueError("Raw ERA5 data does not contain required 'hourly.time' series.")

    times = hourly["time"]
    if not times:
        raise ValueError("Empty time series in ERA5 payload.")

    valid_times = pd.to_datetime(times, utc=True)
    latitude = float(raw_era5.get("latitude", 0.0))
    longitude = float(raw_era5.get("longitude", 0.0))

    var_mapping = {
        "temperature_2m": "degC",
        "surface_pressure": "hPa",
        "wind_speed_10m": "km/h",
    }

    records: List[Dict[str, Any]] = []

    for var_name, unit in var_mapping.items():
        if var_name not in hourly:
            continue

        values = hourly[var_name]
        for i in range(len(times)):
            val = values[i]
            records.append({
                "location": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "valid_time": valid_times[i],
                "variable": var_name,
                "truth_value": float(val) if val is not None and not np.isnan(val) else np.nan,
                "truth_unit": unit,
                "truth_source": truth_source,
            })

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("No recognized variables could be standardized from ERA5 payload.")

    return df


class HistoricalAlignmentEngine:
    """Aligns forecast records with ground-truth verification reference and calculates error metrics."""

    def __init__(self, historical_dir: str = "data/historical"):
        self.historical_dir = Path(historical_dir)

    def align(
        self,
        forecast_df: pd.DataFrame,
        truth_df: pd.DataFrame,
        join_policy: str = "inner",
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Align forecast DataFrame and truth DataFrame on (location, variable, valid_time).

        Args:
            forecast_df: Standardized forecast DataFrame from GEFSStandardizer.
            truth_df: Standardized reference DataFrame from standardize_era5_reference.
            join_policy: Join method ('inner' to only retain fully matched valid times).

        Returns:
            Tuple of (paired_historical_df, alignment_metrics_report).
        """
        if forecast_df.empty or truth_df.empty:
            raise ValueError("Cannot perform alignment on empty forecast or truth DataFrames.")

        f_df = forecast_df.copy()
        t_df = truth_df.copy()

        # Ensure valid_time is timezone-aware UTC datetime
        f_df["valid_time"] = pd.to_datetime(f_df["valid_time"], utc=True)
        t_df["valid_time"] = pd.to_datetime(t_df["valid_time"], utc=True)

        # Prepare forecast columns
        if "value" in f_df.columns and "forecast_value" not in f_df.columns:
            f_df = f_df.rename(columns={"value": "forecast_value", "unit": "forecast_unit", "source": "forecast_source"})

        # Record counts before merge
        total_forecast_rows = len(f_df)
        total_truth_rows = len(t_df)

        # Merge on location, variable, valid_time
        join_keys = ["location", "variable", "valid_time"]
        merged = pd.merge(
            f_df,
            t_df[["location", "variable", "valid_time", "latitude", "longitude", "truth_value", "truth_unit", "truth_source"]],
            on=join_keys,
            how=join_policy,
            suffixes=("", "_truth"),
        )

        if merged.empty:
            raise ValueError("No temporal overlap found between forecast and truth datasets.")

        # Spatial distance between forecast grid point and truth grid point
        merged["spatial_distance_km"] = merged.apply(
            lambda r: haversine_distance_km(r["latitude"], r["longitude"], r["latitude_truth"], r["longitude_truth"]),
            axis=1,
        )

        # Drop temporary truth coordinate column
        if "latitude_truth" in merged.columns:
            merged = merged.drop(columns=["latitude_truth", "longitude_truth"])

        # Calculate forecast errors
        # e = y_hat - y_truth (positive = overprediction, negative = underprediction)
        merged["forecast_error"] = merged["forecast_value"] - merged["truth_value"]
        merged["forecast_abs_error"] = merged["forecast_error"].abs()

        # Ensemble mean errors
        merged["ensemble_mean_error"] = merged["ensemble_mean"] - merged["truth_value"]
        merged["ensemble_mean_abs_error"] = merged["ensemble_mean_error"].abs()

        # Enforce exact column schema
        paired_df = merged[PAIRED_DATASET_COLUMNS].copy()

        # Build diagnostic alignment report
        matched_rows = len(paired_df)
        unmatched_forecast = total_forecast_rows - matched_rows
        unmatched_truth = total_truth_rows - matched_rows

        # Calculate summary error metrics per variable
        metrics_by_var = {}
        for var, group in paired_df.groupby("variable"):
            valid_errors = group["forecast_error"].dropna()
            valid_abs = group["forecast_abs_error"].dropna()
            metrics_by_var[var] = {
                "matched_records": len(group),
                "mean_error_bias": round(float(valid_errors.mean()), 3) if len(valid_errors) > 0 else 0.0,
                "mae": round(float(valid_abs.mean()), 3) if len(valid_abs) > 0 else 0.0,
                "rmse": round(float(np.sqrt((valid_errors ** 2).mean())), 3) if len(valid_errors) > 0 else 0.0,
                "ensemble_mae": round(float(group["ensemble_mean_abs_error"].dropna().mean()), 3) if len(group) > 0 else 0.0,
            }

        report = {
            "alignment_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_forecast_records": total_forecast_rows,
            "total_truth_records": total_truth_rows,
            "matched_paired_records": matched_rows,
            "unmatched_forecast_records": unmatched_forecast,
            "unmatched_truth_records": unmatched_truth,
            "match_rate_pct": round((matched_rows / total_forecast_rows) * 100.0, 2) if total_forecast_rows > 0 else 0.0,
            "mean_spatial_distance_km": round(float(paired_df["spatial_distance_km"].mean()), 3),
            "variable_error_metrics": metrics_by_var,
        }

        return paired_df, report

    def save_paired_dataset(
        self,
        paired_df: pd.DataFrame,
        report: Dict[str, Any],
        location_name: str = "delhi",
        timestamp_str: Optional[str] = None,
    ) -> Tuple[Path, Path, Path]:
        """Save paired historical dataset and alignment manifest to data/historical."""
        if timestamp_str is None:
            timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        dest_dir = self.historical_dir / location_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = dest_dir / f"paired_historical_{location_name}_{timestamp_str}.parquet"
        csv_path = dest_dir / f"paired_historical_{location_name}_{timestamp_str}.csv"
        manifest_path = dest_dir / f"paired_historical_{location_name}_{timestamp_str}_manifest.json"

        paired_df.to_parquet(parquet_path, index=False)
        paired_df.to_csv(csv_path, index=False)

        manifest = {
            "dataset_name": f"Paired Historical Forecast-Verification Dataset ({location_name})",
            "generation_time_utc": datetime.now(timezone.utc).isoformat(),
            "location_name": location_name,
            "total_records": len(paired_df),
            "parquet_file_path": str(parquet_path),
            "csv_file_path": str(csv_path),
            "alignment_summary": report,
        }

        import json
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return parquet_path, csv_path, manifest_path
