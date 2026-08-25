"""
Issue-Time-Safe Feature Pipeline (Phase 3).

Generates tabular features for Medium-Range Weather Forecast Bust Risk Estimation.

SCIENTIFIC CONSTRAINTS & LEAKAGE SAFEGUARDS:
- ALL features must be computable strictly at forecast issue_time.
- Features are derived exclusively from the forecast trajectory, ensemble distribution statistics,
  physical gradients, and issue-time calendar/astronomical timestamps.
- Ground truth / ERA5 observations / future verification errors are STRICTLY FORBIDDEN as features.
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


# Explicit canonical feature list for model training and inference
FEATURE_COLUMN_NAMES = [
    # 1. Ensemble Dispersion & Spread Features
    "ensemble_std",
    "ensemble_range",
    "ensemble_iqr",
    "ensemble_skew_proxy",
    "ensemble_cv",
    "ensemble_spread_to_iqr_ratio",
    "member_count",
    "has_full_ensemble",
    # 2. Forecast Values & Trajectory Gradients
    "forecast_value",
    "ensemble_mean",
    "ensemble_spread_delta_6h",
    "ensemble_spread_delta_24h",
    "forecast_delta_6h",
    "forecast_delta_24h",
    # 3. Horizon & Temporal/Cyclical Features
    "lead_hours",
    "lead_days",
    "valid_hour",
    "valid_month",
    "valid_dayofweek",
    "sin_hour",
    "cos_hour",
    "sin_month",
    "cos_month",
    "is_weekend",
    # 4. Spatial Coordinates
    "latitude",
    "longitude",
]

METADATA_COLUMNS = [
    "location",
    "variable",
    "issue_time",
    "valid_time",
    "lead_hours",
]


class IssueTimeSafeFeaturePipeline:
    """Extracts issue-time safe features from standardized forecast datasets."""

    def __init__(self, eps: float = 1e-6):
        self.eps = eps

    def extract_features(
        self,
        df_forecast: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Transform standardized forecast records into a clean feature matrix X and metadata DataFrame.

        Args:
            df_forecast: Standardized forecast DataFrame (from GEFSStandardizer or Historical paired set).

        Returns:
            Tuple of (features_df, metadata_df).
        """
        if df_forecast.empty:
            raise ValueError("Input DataFrame is empty.")

        df = df_forecast.copy()

        # Normalize column names if needed
        if "value" in df.columns and "forecast_value" not in df.columns:
            df["forecast_value"] = df["value"]

        # Ensure datetime types
        df["valid_time"] = pd.to_datetime(df["valid_time"], utc=True)
        df["issue_time"] = pd.to_datetime(df["issue_time"], utc=True)

        # Sort chronologically by location, variable, and valid_time for trajectory gradient features
        sort_keys = ["location", "variable", "issue_time", "valid_time"]
        avail_sort = [k for k in sort_keys if k in df.columns]
        df = df.sort_values(by=avail_sort).reset_index(drop=True)

        # ---------------------------------------------------------
        # 1. Ensemble Dispersion & Spread Features
        # ---------------------------------------------------------
        ens_std = df["ensemble_std"].fillna(0.0).astype(float)
        ens_mean = df["ensemble_mean"].fillna(df["forecast_value"]).astype(float)
        ens_min = df["ensemble_min"].fillna(ens_mean).astype(float)
        ens_max = df["ensemble_max"].fillna(ens_mean).astype(float)
        q10 = df["q10"].fillna(ens_min).astype(float)
        q90 = df["q90"].fillna(ens_max).astype(float)

        df["ensemble_range"] = (ens_max - ens_min).clip(lower=0.0)
        df["ensemble_iqr"] = (q90 - q10).clip(lower=0.0)
        
        # Ensemble skewness proxy: (mean - midpoint) / (std + eps)
        midpoint = 0.5 * (ens_max + ens_min)
        df["ensemble_skew_proxy"] = (ens_mean - midpoint) / (ens_std + self.eps)

        # Coefficient of variation: std / (|mean| + eps)
        df["ensemble_cv"] = ens_std / (ens_mean.abs() + self.eps)

        # Ratio of spread to IQR
        df["ensemble_spread_to_iqr_ratio"] = ens_std / (df["ensemble_iqr"] + self.eps)

        # Member count flags
        df["member_count"] = df["member_count"].fillna(31).astype(int)
        df["has_full_ensemble"] = (df["member_count"] == 31).astype(int)

        # ---------------------------------------------------------
        # 2. Trajectory Rate of Change / Gradients (along forecast valid time)
        # ---------------------------------------------------------
        # Compute forward forecast gradients along lead time
        group_cols = [c for c in ["location", "variable", "issue_time"] if c in df.columns]

        df["forecast_delta_6h"] = df.groupby(group_cols)["forecast_value"].diff(periods=6).fillna(0.0)
        df["forecast_delta_24h"] = df.groupby(group_cols)["forecast_value"].diff(periods=24).fillna(0.0)
        df["ensemble_spread_delta_6h"] = df.groupby(group_cols)["ensemble_std"].diff(periods=6).fillna(0.0)
        df["ensemble_spread_delta_24h"] = df.groupby(group_cols)["ensemble_std"].diff(periods=24).fillna(0.0)

        # ---------------------------------------------------------
        # 3. Horizon & Temporal/Cyclical Features
        # ---------------------------------------------------------
        df["lead_hours"] = df["lead_hours"].astype(int)
        df["lead_days"] = (df["lead_hours"] / 24.0).round(3)

        valid_hour = df["valid_time"].dt.hour
        valid_month = df["valid_time"].dt.month
        valid_dow = df["valid_time"].dt.dayofweek

        df["valid_hour"] = valid_hour
        df["valid_month"] = valid_month
        df["valid_dayofweek"] = valid_dow
        df["is_weekend"] = valid_dow.isin([5, 6]).astype(int)

        # Cyclical trigonometry transformations
        df["sin_hour"] = np.sin(2 * np.pi * valid_hour / 24.0).round(5)
        df["cos_hour"] = np.cos(2 * np.pi * valid_hour / 24.0).round(5)
        df["sin_month"] = np.sin(2 * np.pi * valid_month / 12.0).round(5)
        df["cos_month"] = np.cos(2 * np.pi * valid_month / 12.0).round(5)

        # ---------------------------------------------------------
        # 4. Spatial Coordinates
        # ---------------------------------------------------------
        df["latitude"] = df["latitude"].astype(float)
        df["longitude"] = df["longitude"].astype(float)

        # Build feature DataFrame and metadata DataFrame
        X = df[FEATURE_COLUMN_NAMES].copy()
        
        # Replace any inf / -inf with nan and fill
        X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        meta_cols_present = [c for c in METADATA_COLUMNS if c in df.columns]
        metadata = df[meta_cols_present].copy()

        return X, metadata
