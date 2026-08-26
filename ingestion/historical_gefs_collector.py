"""
NOAA GEFS S3 Historical Forecast Collector.

Extracts genuine historical GEFS ensemble forecasts (31 members, 0-72h horizon)
directly from NOAA's AWS S3 bucket (noaa-gefs-pds) using .idx byte-range extraction
and ecCodes decoding.
"""

import concurrent.futures
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from ingestion.collector import GEFSCollector


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two coordinates in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 3)


class HistoricalGEFSCollector:
    """Collector for genuine historical NOAA GEFS ensemble forecasts from AWS S3."""

    BASE_S3_URL = "https://noaa-gefs-pds.s3.amazonaws.com"
    DEFAULT_MEMBERS = ["gec00"] + [f"gep{i:02d}" for i in range(1, 31)] # 31 members

    def __init__(
        self,
        raw_dir: str = "data/raw/gefs_historical",
        processed_dir: str = "data/processed/gefs_historical",
        python_eccodes_runner: str = "scratch/micromamba.exe",
        env_eccodes_path: str = "scratch/env_eccodes",
        max_workers: int = 20,
    ):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.python_eccodes_runner = Path(python_eccodes_runner)
        self.env_eccodes_path = Path(env_eccodes_path)
        self.max_workers = max_workers

    def collect_range(
        self,
        start_date: str = "2026-08-18",
        end_date: str = "2026-08-24",
        cycle: str = "00",
        horizon_hours: int = 72,
        step_hours: int = 3,
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        location_name: str = "delhi",
        use_cache: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any], Path, Path]:
        """
        Collect genuine historical GEFS ensemble forecasts for a range of dates.
        """
        now_utc = datetime.now(timezone.utc)
        sub_folder = f"{start_date}_{end_date}"
        dest_raw_dir = self.raw_dir / location_name / sub_folder
        dest_proc_dir = self.processed_dir / location_name / sub_folder
        dest_raw_dir.mkdir(parents=True, exist_ok=True)
        dest_proc_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = now_utc.strftime("%Y%m%dT%H%M%SZ")
        raw_file_path = dest_raw_dir / f"gefs_historical_raw_{location_name}_{timestamp_str}.json"
        manifest_file_path = dest_raw_dir / f"gefs_historical_raw_{location_name}_{timestamp_str}_manifest.json"

        # 1. Authoritative S3 Cycle Verification
        gefs_base_collector = GEFSCollector()
        verified_cycles = gefs_base_collector.query_range_cycles(start_date, end_date)
        for ds, v_info in verified_cycles.items():
            if v_info.get("status") != "VERIFIED":
                raise RuntimeError(f"Date {ds} could not be verified on NOAA S3 registry: {v_info.get('error')}")

        # Compute nearest grid point coordinates (GEFS 0.5 deg global grid)
        grid_lat = round(latitude * 2) / 2 # e.g. 28.5
        grid_lon = round(longitude * 2) / 2 # e.g. 77.0
        lat_idx = int(round((90.0 - grid_lat) / 0.5))
        lon_idx = int(round(grid_lon / 0.5))
        flat_idx = lat_idx * 720 + lon_idx
        spatial_dist_km = haversine_distance_km(latitude, longitude, grid_lat, grid_lon)

        d_start = datetime.strptime(start_date.replace("-", "")[:8], "%Y%m%d")
        d_end = datetime.strptime(end_date.replace("-", "")[:8], "%Y%m%d")

        dates: List[str] = []
        curr = d_start
        while curr <= d_end:
            dates.append(curr.strftime("%Y%m%d"))
            curr += timedelta(days=1)

        steps = [f"f{h:03d}" for h in range(0, horizon_hours + 1, step_hours)]
        members = self.DEFAULT_MEMBERS

        # Cache check
        extracted_data = None
        if use_cache:
            existing_raw = sorted(list(dest_raw_dir.glob("gefs_historical_raw_*.json")))
            data_files = [f for f in existing_raw if not f.name.endswith("_manifest.json")]
            for ef in reversed(data_files):
                try:
                    with open(ef, "r", encoding="utf-8") as f:
                        cached_json = json.load(f)
                    # Check if all dates are present
                    if all(d in cached_json for d in dates):
                        print(f"[NOAA GEFS Historical Collector] Reusing existing raw extraction cache: {ef}")
                        extracted_data = cached_json
                        raw_file_path = ef
                        break
                except Exception:
                    continue

        if extracted_data is None:
            print(f"[NOAA GEFS Historical Collector] Fetching {len(dates)} dates x {len(steps)} steps x {len(members)} members = {len(dates)*len(steps)*len(members)} files from NOAA S3...")

            task_config = {
                "dates": dates,
                "cycle": cycle,
                "steps": steps,
                "members": members,
                "grid_flat_idx": flat_idx,
                "max_workers": self.max_workers,
                "output_json": str(raw_file_path),
            }
            config_path = dest_raw_dir / f"task_config_{timestamp_str}.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(task_config, f, indent=2)

            worker_script = Path("ingestion/s3_eccodes_worker.py")
            cmd = [
                str(self.python_eccodes_runner),
                "run",
                "-p",
                str(self.env_eccodes_path),
                "python",
                str(worker_script),
                str(config_path),
            ]

            t0 = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True)
            t1 = time.time()

            if result.returncode != 0:
                raise RuntimeError(f"ecCodes S3 worker failed with code {result.returncode}:\nStdout: {result.stdout}\nStderr: {result.stderr}")

            print(f"[NOAA GEFS Historical Collector] Extraction completed in {t1 - t0:.2f}s.")

            with open(raw_file_path, "r", encoding="utf-8") as f:
                extracted_data = json.load(f)

            if config_path.exists():
                config_path.unlink()

        # 4. Standardize into Canonical Project Schema
        records: List[Dict[str, Any]] = []

        var_metadata = {
            "temperature_2m": {"unit": "degC", "source": "NOAA_GEFS_S3_HISTORICAL"},
            "surface_pressure": {"unit": "hPa", "source": "NOAA_GEFS_S3_HISTORICAL"},
            "wind_speed_10m": {"unit": "km/h", "source": "NOAA_GEFS_S3_HISTORICAL"},
        }

        for date_str in sorted(extracted_data.keys()):
            issue_dt = datetime.strptime(f"{date_str}{cycle}", "%Y%m%d%H").replace(tzinfo=timezone.utc)

            date_data = extracted_data[date_str]
            for step in sorted(date_data.keys()):
                lead_h = int(step.replace("f", ""))
                valid_dt = issue_dt + timedelta(hours=lead_h)

                member_dict = date_data[step]
                if not member_dict:
                    continue

                for var_name, v_meta in var_metadata.items():
                    member_vals = []
                    control_val = None

                    for m in members:
                        if m in member_dict and var_name in member_dict[m]:
                            val = member_dict[m][var_name]
                            if val is not None and not math.isnan(val):
                                member_vals.append(val)
                                if m == "gec00":
                                    control_val = val

                    if not member_vals:
                        continue

                    arr = np.array(member_vals, dtype=float)
                    n_m = len(arr)
                    ens_mean = float(np.mean(arr))
                    ens_std = float(np.std(arr, ddof=1)) if n_m > 1 else 0.0
                    ens_min = float(np.min(arr))
                    ens_max = float(np.max(arr))
                    ens_q10 = float(np.percentile(arr, 10))
                    ens_q90 = float(np.percentile(arr, 90))

                    if control_val is None:
                        control_val = ens_mean

                    records.append({
                        "location": location_name,
                        "latitude": latitude,
                        "longitude": longitude,
                        "issue_time": issue_dt,
                        "valid_time": valid_dt,
                        "lead_hours": lead_h,
                        "variable": var_name,
                        "value": control_val,
                        "unit": v_meta["unit"],
                        "source": v_meta["source"],
                        "member_id": "ensemble_summary",
                        "ensemble_mean": ens_mean,
                        "ensemble_std": ens_std,
                        "ensemble_min": ens_min,
                        "ensemble_max": ens_max,
                        "q10": ens_q10,
                        "q90": ens_q90,
                        "member_count": n_m,
                    })

        df_forecast = pd.DataFrame(records)
        if df_forecast.empty:
            raise ValueError("No forecast records could be extracted from historical GEFS S3 data.")

        required_cols = [
            "location", "latitude", "longitude", "issue_time", "valid_time", "lead_hours",
            "variable", "value", "unit", "source", "member_id", "ensemble_mean",
            "ensemble_std", "ensemble_min", "ensemble_max", "q10", "q90", "member_count"
        ]
        df_forecast = df_forecast[required_cols]

        # 5. Save Processed Files & Build Provenance Manifest
        proc_parquet = dest_proc_dir / f"gefs_historical_{location_name}_{timestamp_str}.parquet"
        proc_csv = dest_proc_dir / f"gefs_historical_{location_name}_{timestamp_str}.csv"
        df_forecast.to_parquet(proc_parquet, index=False)
        df_forecast.to_csv(proc_csv, index=False)

        raw_bytes = raw_file_path.read_bytes()
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        manifest = {
            "source": "NOAA NCEP GEFS AWS S3 Open Data (noaa-gefs-pds)",
            "collection_method": "HTTP Range Byte-Slice Extraction (.idx) + ECMWF ecCodes Decoder",
            "decoder": "ecCodes (via isolated micromamba environment)",
            "location_name": location_name,
            "requested_coordinates": {"latitude": latitude, "longitude": longitude},
            "actual_grid_coordinates": {"latitude": grid_lat, "longitude": grid_lon},
            "spatial_distance_km": spatial_dist_km,
            "start_date": start_date,
            "end_date": end_date,
            "cycle": f"{cycle}z",
            "total_distinct_cycles": len(dates),
            "horizon_hours": horizon_hours,
            "step_hours": step_hours,
            "lead_steps_count": len(steps),
            "ensemble_members_count": len(members),
            "total_standardized_rows": len(df_forecast),
            "verified_s3_cycles": verified_cycles,
            "download_time_utc": now_utc.isoformat(),
            "raw_file_path": str(raw_file_path),
            "processed_parquet_path": str(proc_parquet),
            "processed_csv_path": str(proc_csv),
            "sha256_checksum": sha256_hash,
            "byte_size": len(raw_bytes),
        }

        with open(manifest_file_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return df_forecast, manifest, raw_file_path, manifest_file_path
