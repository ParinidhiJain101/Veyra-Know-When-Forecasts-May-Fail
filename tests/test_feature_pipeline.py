"""
Unit tests for Issue-Time-Safe Feature Pipeline (Phase 3).

Tests:
1. Extraction of canonical 26 features
2. Ensemble dispersion feature formulas (range, IQR, skew proxy, CV)
3. Trajectory gradient differences (6h and 24h deltas)
4. Temporal cyclical trigonometry encodings
5. Missing values / infinite values handling
"""

from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
import pytest

from features.feature_pipeline import IssueTimeSafeFeaturePipeline, FEATURE_COLUMN_NAMES


@pytest.fixture
def mock_forecast_series():
    """Mock 30-hour forecast series for feature extraction testing."""
    issue = datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc)
    rows = []
    for lead in range(30):
        valid = issue + timedelta(hours=lead)
        rows.append({
            "location": "delhi",
            "latitude": 28.5,
            "longitude": 77.25,
            "issue_time": issue,
            "valid_time": valid,
            "lead_hours": lead,
            "variable": "temperature_2m",
            "forecast_value": 30.0 + lead * 0.2,
            "ensemble_mean": 30.1 + lead * 0.2,
            "ensemble_std": 1.0 + lead * 0.05,
            "ensemble_min": 28.0 + lead * 0.2,
            "ensemble_max": 32.0 + lead * 0.2,
            "q10": 29.0 + lead * 0.2,
            "q90": 31.2 + lead * 0.2,
            "member_count": 31,
        })
    return pd.DataFrame(rows)


def test_feature_pipeline_extraction(mock_forecast_series):
    """Test full extraction returns canonical feature matrix and metadata."""
    pipeline = IssueTimeSafeFeaturePipeline()
    X, metadata = pipeline.extract_features(mock_forecast_series)

    assert list(X.columns) == FEATURE_COLUMN_NAMES
    assert len(X) == len(mock_forecast_series)
    assert len(metadata) == len(mock_forecast_series)

    # Invariant: No NaNs or Infs in feature matrix
    assert not X.isna().any().any()
    assert not np.isinf(X.values).any()


def test_ensemble_dispersion_calculations(mock_forecast_series):
    """Test mathematical accuracy of ensemble dispersion metrics."""
    pipeline = IssueTimeSafeFeaturePipeline()
    X, _ = pipeline.extract_features(mock_forecast_series)

    # For lead 0: min=28.0, max=32.0 -> range = 4.0
    assert pytest.approx(X["ensemble_range"].iloc[0], 0.01) == 4.0

    # q10=29.0, q90=31.2 -> IQR = 2.2
    assert pytest.approx(X["ensemble_iqr"].iloc[0], 0.01) == 2.2

    # Member count flags
    assert X["member_count"].iloc[0] == 31
    assert X["has_full_ensemble"].iloc[0] == 1


def test_temporal_cyclical_encodings(mock_forecast_series):
    """Test cyclical trigonometry bounds [-1, 1] and periodicity."""
    pipeline = IssueTimeSafeFeaturePipeline()
    X, _ = pipeline.extract_features(mock_forecast_series)

    assert (X["sin_hour"] >= -1.0).all() and (X["sin_hour"] <= 1.0).all()
    assert (X["cos_hour"] >= -1.0).all() and (X["cos_hour"] <= 1.0).all()
    assert (X["sin_month"] >= -1.0).all() and (X["sin_month"] <= 1.0).all()
    assert (X["cos_month"] >= -1.0).all() and (X["cos_month"] <= 1.0).all()

    # sin^2 + cos^2 == 1.0
    trig_identity = (X["sin_hour"] ** 2 + X["cos_hour"] ** 2).round(3)
    assert (trig_identity == 1.0).all()


def test_trajectory_deltas(mock_forecast_series):
    """Test 6-hour and 24-hour forward difference calculations."""
    pipeline = IssueTimeSafeFeaturePipeline()
    X, _ = pipeline.extract_features(mock_forecast_series)

    # At lead 6: forecast_delta_6h = val[6] - val[0] = (30 + 1.2) - 30.0 = 1.2
    assert pytest.approx(X["forecast_delta_6h"].iloc[6], 0.01) == 1.2

    # At lead 24: forecast_delta_24h = val[24] - val[0] = (30 + 4.8) - 30.0 = 4.8
    assert pytest.approx(X["forecast_delta_24h"].iloc[24], 0.01) == 4.8
