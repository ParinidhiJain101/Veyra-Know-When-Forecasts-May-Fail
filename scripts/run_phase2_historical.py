"""
Phase 2 Execution Script — Historical Forecast/Reference Alignment & Error Engine.

Executes end-to-end:
1. Ingest/Load Historical GEFS Forecasts (Delhi)
2. Ingest/Load Historical ERA5 Reanalysis Ground Truth
3. Standardize Both Datasets
4. Align by Location, Variable, and Valid Time under Spatial Colocation Policy
5. Compute Forecast Error, Absolute Error, and Ensemble Mean Errors
6. Persist Paired Historical Dataset to data/historical/
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.collector import GEFSCollector
from ingestion.era5_collector import ERA5ReferenceCollector
from data_pipeline.standardize import GEFSStandardizer
from data_pipeline.historical_aligner import HistoricalAlignmentEngine, standardize_era5_reference


def run_historical_alignment(
    location_name: str = "delhi",
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    start_date: str = "2026-08-20",
    end_date: str = "2026-08-24",
    use_cache: bool = False,
) -> int:
    print("=" * 75)
    print(" FORECAST-BUST SENTINEL — PHASE 2: HISTORICAL ALIGNMENT & ERROR ENGINE")
    print("=" * 75)
    print(f"Target Location  : {location_name.upper()} (Lat: {latitude:.4f}, Lon: {longitude:.4f})")
    print(f"Historical Window: {start_date} to {end_date}")
    print(f"Forecast Model   : NOAA GEFS 0.25 deg Ensemble (31 members)")
    print(f"Truth Reference  : ECMWF ERA5 Reanalysis (Open-Meteo Historical Archive)")
    print(f"Cache Mode       : {'Reusing local cache if available' if use_cache else 'Live download from source endpoints'}")
    print("-" * 75)

    # 1. Ingest Historical GEFS Forecast
    print("\n[STEP 1/5] INGESTION — Fetching Historical GEFS Forecast...")
    gefs_collector = GEFSCollector()
    try:
        # For historical runs, query start_date cycle
        issue_time_anchor = f"{start_date}T00:00:00+00:00"
        raw_gefs, raw_gefs_path, gefs_manifest_path, gefs_manifest = gefs_collector.fetch_forecast(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            start_date=start_date,
            end_date=end_date,
            issue_time=issue_time_anchor,
            use_cache=use_cache,
        )
        print(f"  [OK] Historical GEFS raw preserved : {raw_gefs_path}")
        print(f"  [OK] Explicit Issue Time           : {gefs_manifest.get('explicit_issue_time_utc')}")
    except Exception as e:
        print(f"[ERROR] Failed to ingest historical GEFS data: {e}", file=sys.stderr)
        return 1

    # 2. Ingest Historical ERA5 Truth Reference
    print("\n[STEP 2/5] INGESTION — Fetching Historical ERA5 Truth Reference...")
    era5_collector = ERA5ReferenceCollector()
    try:
        raw_era5, raw_era5_path, era5_manifest_path, era5_manifest = era5_collector.fetch_historical_reference(
            start_date=start_date,
            end_date=end_date,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            use_cache=use_cache,
        )
        print(f"  [OK] Historical ERA5 raw preserved : {raw_era5_path}")
        print(f"  [OK] Hourly records retrieved      : {era5_manifest.get('hourly_record_count')}")
    except Exception as e:
        print(f"[ERROR] Failed to ingest ERA5 reference data: {e}", file=sys.stderr)
        return 1

    # 3. Standardize Both
    print("\n[STEP 3/5] STANDARDIZATION — Normalizing Forecast & Truth Datasets...")
    try:
        standardizer = GEFSStandardizer()
        df_forecast = standardizer.standardize(
            raw_gefs,
            issue_time=gefs_manifest["explicit_issue_time_utc"],
            location_name=location_name,
            filter_future_only=True,
        )
        df_truth = standardize_era5_reference(
            raw_era5,
            location_name=location_name,
        )
        print(f"  [OK] Standardized Forecast Records: {len(df_forecast)}")
        print(f"  [OK] Standardized Truth Records   : {len(df_truth)}")
    except Exception as e:
        print(f"[ERROR] Standardization failed: {e}", file=sys.stderr)
        return 1

    # 4. Alignment & Error Calculation
    print("\n[STEP 4/5] ALIGNMENT & ERROR CALCULATION — Matching on (location, variable, valid_time)...")
    aligner = HistoricalAlignmentEngine()
    try:
        df_paired, alignment_report = aligner.align(df_forecast, df_truth, join_policy="inner")
        print(f"  [OK] Matched Paired Records       : {alignment_report['matched_paired_records']} ({alignment_report['match_rate_pct']}%)")
        print(f"  [OK] Mean Spatial Colocation Dist : {alignment_report['mean_spatial_distance_km']} km")
        print("  [OK] Error Metrics Summary by Variable:")
        for var, metrics in alignment_report["variable_error_metrics"].items():
            print(f"      - {var.ljust(20)}: Mean Bias={metrics['mean_error_bias']:+.2f}, MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, Ens_MAE={metrics['ensemble_mae']:.2f}")
    except Exception as e:
        print(f"[ERROR] Alignment failed: {e}", file=sys.stderr)
        return 1

    # 5. Persist Paired Dataset
    print("\n[STEP 5/5] STORAGE — Persisting Paired Historical Dataset...")
    parquet_p, csv_p, manifest_p = aligner.save_paired_dataset(df_paired, alignment_report, location_name=location_name)
    print(f"  [OK] Paired Parquet saved : {parquet_p} ({parquet_p.stat().st_size / 1024.0:.2f} KB)")
    print(f"  [OK] Paired CSV saved     : {csv_p} ({csv_p.stat().st_size / 1024.0:.2f} KB)")
    print(f"  [OK] Alignment manifest   : {manifest_p}")

    # Print Sample Paired Row
    print("\n" + "=" * 75)
    print(" SAMPLE HISTORICAL PAIRED RECORD (FULL COLUMNS)")
    print("=" * 75)
    sample_row = df_paired.iloc[0].to_dict()
    for col, val in sample_row.items():
        print(f"  {col.ljust(26)} : {val}")

    print("\n" + "=" * 75)
    print(" PHASE 2 HISTORICAL ALIGNMENT COMPLETED SUCCESSFULLY")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Forecast-Bust Sentinel Phase 2 Historical Pipeline")
    parser.add_argument("--location", default="delhi", help="Location name")
    parser.add_argument("--lat", type=float, default=28.6139, help="Latitude")
    parser.add_argument("--lon", type=float, default=77.2090, help="Longitude")
    parser.add_argument("--start-date", default="2026-08-20", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default="2026-08-24", help="End date (YYYY-MM-DD)")
    parser.add_argument("--use-cache", action="store_true", help="Reuse local raw cache if available")
    args = parser.parse_args()

    sys.exit(run_historical_alignment(
        location_name=args.location,
        latitude=args.lat,
        longitude=args.lon,
        start_date=args.start_date,
        end_date=args.end_date,
        use_cache=args.use_cache,
    ))
