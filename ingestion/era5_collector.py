"""
ERA5 Historical Reanalysis Collector.

Retrieves historical verification ground-truth reference records from ECMWF ERA5
via the Open-Meteo Historical Weather Archive API.

SCIENTIFIC CONSTRAINT:
This reference data is exclusively used for offline historical alignment, forecast error
computation, and verification labeling. It must NEVER be used as a live feature at issue time.
"""

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ERA5ReferenceCollector:
    """Collector for ERA5 historical reanalysis verification data."""

    DEFAULT_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(
        self,
        raw_dir: str = "data/raw/era5",
        timeout_seconds: int = 30,
    ):
        self.raw_dir = Path(raw_dir)
        self.timeout_seconds = timeout_seconds

    def fetch_historical_reference(
        self,
        start_date: str,  # Format: "YYYY-MM-DD"
        end_date: str,    # Format: "YYYY-MM-DD"
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        location_name: str = "delhi",
        variables: Optional[List[str]] = None,
        use_cache: bool = False,
    ) -> Tuple[Dict[str, Any], Path, Path, Dict[str, Any]]:
        """
        Fetch historical ERA5 reference data for a given location and date range.

        Args:
            start_date: Start date string (YYYY-MM-DD).
            end_date: End date string (YYYY-MM-DD).
            latitude: Latitude of target location.
            longitude: Longitude of target location.
            location_name: Descriptive name of the target location.
            variables: List of variable keys to request.
            use_cache: If True, look for an existing raw file matching the date range first.

        Returns:
            Tuple of (raw_data_dict, raw_file_path, manifest_path, manifest_dict).
        """
        if variables is None:
            variables = ["temperature_2m", "surface_pressure", "wind_speed_10m"]

        now_utc = datetime.now(timezone.utc)
        dest_dir = self.raw_dir / location_name / f"{start_date}_{end_date}"
        dest_dir.mkdir(parents=True, exist_ok=True)

        if use_cache:
            existing_files = list(dest_dir.glob("era5_raw_*.json"))
            existing_data_files = [f for f in existing_files if not f.name.endswith("_manifest.json")]
            if existing_data_files:
                latest_raw = sorted(existing_data_files)[-1]
                manifest_path = latest_raw.parent / f"{latest_raw.stem}_manifest.json"
                if manifest_path.exists():
                    with open(latest_raw, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    return raw_data, latest_raw, manifest_path, manifest

        # Build query parameters
        vars_param = ",".join(variables)
        params = (
            f"?latitude={latitude:.4f}"
            f"&longitude={longitude:.4f}"
            f"&start_date={start_date}"
            f"&end_date={end_date}"
            f"&hourly={vars_param}"
        )
        url = f"{self.DEFAULT_BASE_URL}{params}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ForecastBustSentinel/1.0 (Historical Verification Reference; ERA5)",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                if response.status != 200:
                    raise RuntimeError(f"ERA5 reference source returned HTTP status {response.status}")
                raw_bytes = response.read()
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve ERA5 historical reference from {url}: {e}") from e

        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        try:
            raw_data = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Received malformed JSON from ERA5 endpoint: {e}") from e

        if "error" in raw_data and raw_data["error"]:
            reason = raw_data.get("reason", "Unknown API error")
            raise RuntimeError(f"ERA5 reference source returned API error: {reason}")

        # Save untouched raw file
        timestamp_str = now_utc.strftime("%Y%m%dT%H%M%SZ")
        raw_file_name = f"era5_raw_{location_name}_{start_date}_{end_date}_{timestamp_str}.json"
        raw_file_path = dest_dir / raw_file_name

        with open(raw_file_path, "wb") as f:
            f.write(raw_bytes)

        time_series = raw_data.get("hourly", {}).get("time", [])
        actual_record_count = len(time_series)

        # Provenance metadata manifest
        manifest = {
            "source": "ECMWF ERA5 Atmospheric Reanalysis via Open-Meteo Historical Archive",
            "provider": "ECMWF / Open-Meteo",
            "role": "Ground Truth Verification Reference (NEVER live feature)",
            "exact_endpoint": self.DEFAULT_BASE_URL,
            "date_range": {"start_date": start_date, "end_date": end_date},
            "download_time_utc": now_utc.isoformat(),
            "location_name": location_name,
            "requested_coordinates": {"latitude": latitude, "longitude": longitude},
            "actual_grid_coordinates": {
                "latitude": raw_data.get("latitude"),
                "longitude": raw_data.get("longitude"),
                "elevation": raw_data.get("elevation"),
            },
            "spatial_colocation_policy": "Nearest grid-point colocation to requested coordinates",
            "variables_requested": variables,
            "hourly_record_count": actual_record_count,
            "first_valid_time": time_series[0] if time_series else None,
            "last_valid_time": time_series[-1] if time_series else None,
            "raw_file_path": str(raw_file_path),
            "sha256_checksum": sha256_hash,
            "byte_size": len(raw_bytes),
        }

        manifest_path = dest_dir / f"era5_raw_{location_name}_{start_date}_{end_date}_{timestamp_str}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return raw_data, raw_file_path, manifest_path, manifest
