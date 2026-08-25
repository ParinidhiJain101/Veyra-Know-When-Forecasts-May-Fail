# Forecast-Bust Sentinel — Builder 2 (Day 1: Forecast Data Foundation)

## Overview
Forecast-Bust Sentinel is an issue-time-safe meta-forecasting platform that predicts when an existing medium-range NWP forecast is likely to fail materially over an India-focused domain.

Day 1 implements the core **Forecast Ingestion & Standardization Foundation**:
```
Location (Delhi) -> Real NOAA GEFS Ingestion -> Raw Preservation & Manifest -> Standardization -> QC Validation -> Standardized Output (Parquet/CSV)
```

## Architecture & Data Flow (Day 1)
- **Source**: NOAA Global Ensemble Forecast System (GEFS) 0.25° ensemble (31 members: 1 control + 30 perturbed).
- **Test Domain**: Delhi, India (Lat: 28.6139°N, Lon: 77.2090°E).
- **Day 1 Variables**:
  - `temperature_2m` (°C)
  - `surface_pressure` (hPa)
  - `wind_speed_10m` (km/h)
- **Timing Invariants**:
  - `issue_time`: Forecast cycle initialization time (UTC)
  - `valid_time`: Predicted target time (UTC)
  - `lead_hours`: Exact integer hours ($valid\_time - issue\_time$)
- **Ensemble Summary**: Preserves mean, standard deviation, minimum, maximum, 10th percentile (`q10`), 90th percentile (`q90`), and member count (`31`).
- **Quality Control (QC)**: 7 automated validation rules with explicit flagging (missing values, duplicates, invalid timestamps, unit mismatch, missing members, stale data, out-of-range bounds).

## Directory Structure
```
forecast-bust-sentinel/
├── configs/
│   └── data_sources.yaml            # GEFS source and variable definitions
├── ingestion/
│   ├── __init__.py
│   └── collector.py                 # Real GEFS collector & provenance manifest
├── data_pipeline/
│   ├── __init__.py
│   ├── standardize.py               # Schema standardization layer
│   └── qc.py                        # 7-rule Quality Control engine
├── scripts/
│   └── run_day1_pipeline.py         # End-to-end CLI execution entrypoint
├── tests/
│   ├── __init__.py
│   ├── test_standardize.py          # Unit tests for standardization
│   ├── test_qc.py                   # Unit tests for 7 QC checks
│   └── test_smoke.py                # Real-data smoke test (reusable cache)
├── data/                            # Excluded from Git (.gitignore)
│   ├── raw/gefs/                    # Untouched source JSON + manifests
│   └── processed/gefs/              # Standardized Parquet + CSV files
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Quickstart

### 1. Installation
```powershell
pip install -r requirements.txt
```

### 2. Run Unit Tests (Offline)
```powershell
python -m pytest tests/test_standardize.py tests/test_qc.py -v
```

### 3. Run Real-Data Smoke Test
```powershell
python -m pytest tests/test_smoke.py -v
```

### 4. Run End-to-End Pipeline
```powershell
python scripts/run_day1_pipeline.py --location delhi --days 3
```
Or reuse cached download:
```powershell
python scripts/run_day1_pipeline.py --location delhi --days 3 --use-cache
```

## Output Schema
| Field | Type | Description |
|---|---|---|
| `location` | str | Target location identifier (e.g. `delhi`) |
| `latitude` | float | Grid cell latitude (28.5°N) |
| `longitude` | float | Grid cell longitude (77.25°E) |
| `issue_time` | datetime (UTC) | Forecast run initialization timestamp |
| `valid_time` | datetime (UTC) | Future target timestamp |
| `lead_hours` | int | Lead time in hours |
| `variable` | str | Standardized variable name |
| `value` | float | Control forecast value |
| `unit` | str | Physical unit (`degC`, `hPa`, `km/h`) |
| `source` | str | Data source (`NOAA_GEFS`) |
| `member_id` | str | Ensemble member identifier (`ensemble_summary`) |
| `ensemble_mean` | float | Mean across 31 ensemble members |
| `ensemble_std` | float | Spread / standard deviation across members |
| `ensemble_min` | float | Minimum member value |
| `ensemble_max` | float | Maximum member value |
| `q10` | float | 10th percentile member value |
| `q90` | float | 90th percentile member value |
| `member_count` | int | Total ensemble members (31) |
