"""
Location Registry and Spatial Colocation Service (Day 6).

Resolves requested geographic coordinates to actual NWP forecast grid points,
computes explicit spatial mismatch distance (km), and manages regional groupings.

SCIENTIFIC INTEGRITY RULE:
- Delhi is the single verified historical NWP location in the current pilot dataset.
- Other registered monitoring locations represent geographical entities. If actual
  forecast grid coordinates are not supplied by the source dataset, actual_grid_coordinates
  and spatial_distance_km remain unresolved (None) rather than fabricated.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from api.schemas import LocationCoordinates, LocationInfo


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth in kilometers.

    Args:
        lat1, lon1: Latitude and longitude of point 1 in degrees.
        lat2, lon2: Latitude and longitude of point 2 in degrees.

    Returns:
        Distance in kilometers.
    """
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class LocationRegistry:
    """Registry of known monitoring points and spatial metadata."""

    # Default registered locations (Delhi retains verified pilot grid point; others require source-resolution)
    DEFAULT_LOCATIONS: Dict[str, Dict[str, Any]] = {
        "delhi": {
            "location_id": "delhi",
            "country": "India",
            "state_region": "National Capital Region",
            "city": "Delhi",
            "requested_latitude": 28.6139,
            "requested_longitude": 77.2090,
            "verified_grid_latitude": 28.50,
            "verified_grid_longitude": 77.25,
        },
        "mumbai": {
            "location_id": "mumbai",
            "country": "India",
            "state_region": "Maharashtra",
            "city": "Mumbai",
            "requested_latitude": 19.0760,
            "requested_longitude": 72.8777,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
        },
        "kolkata": {
            "location_id": "kolkata",
            "country": "India",
            "state_region": "West Bengal",
            "city": "Kolkata",
            "requested_latitude": 22.5726,
            "requested_longitude": 88.3639,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
        },
        "chennai": {
            "location_id": "chennai",
            "country": "India",
            "state_region": "Tamil Nadu",
            "city": "Chennai",
            "requested_latitude": 13.0827,
            "requested_longitude": 80.2707,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
        },
        "bengaluru": {
            "location_id": "bengaluru",
            "country": "India",
            "state_region": "Karnataka",
            "city": "Bengaluru",
            "requested_latitude": 12.9716,
            "requested_longitude": 77.5946,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
        },
    }

    def __init__(self, custom_locations: Optional[Dict[str, Dict[str, Any]]] = None):
        self._locations = dict(self.DEFAULT_LOCATIONS)
        if custom_locations:
            self._locations.update(custom_locations)

    def get_location(
        self,
        location_id: str,
        actual_grid_lat: Optional[float] = None,
        actual_grid_lon: Optional[float] = None,
    ) -> LocationInfo:
        """
        Retrieve location info, resolving the spatial offset if actual grid coordinates exist.

        Args:
            location_id: Identifier of the location (case-insensitive).
            actual_grid_lat: Actual grid latitude from forecast source metadata.
            actual_grid_lon: Actual grid longitude from forecast source metadata.

        Returns:
            LocationInfo dataclass.
        """
        loc_key = location_id.strip().lower()
        if loc_key not in self._locations:
            raise KeyError(f"Unknown location_id '{location_id}'. Registered locations: {list(self._locations.keys())}")

        cfg = self._locations[loc_key]
        req_lat = cfg["requested_latitude"]
        req_lon = cfg["requested_longitude"]

        # Resolve actual grid coordinate: caller override > verified pilot grid coordinate > None
        grid_lat = actual_grid_lat if actual_grid_lat is not None else cfg.get("verified_grid_latitude")
        grid_lon = actual_grid_lon if actual_grid_lon is not None else cfg.get("verified_grid_longitude")

        if grid_lat is not None and grid_lon is not None:
            actual_coords = LocationCoordinates(latitude=grid_lat, longitude=grid_lon)
            dist_km = haversine_distance_km(req_lat, req_lon, grid_lat, grid_lon)
        else:
            actual_coords = None
            dist_km = None

        return LocationInfo(
            location_id=cfg["location_id"],
            country=cfg["country"],
            state_region=cfg["state_region"],
            city=cfg["city"],
            requested_coordinates=LocationCoordinates(latitude=req_lat, longitude=req_lon),
            actual_grid_coordinates=actual_coords,
            spatial_distance_km=dist_km,
        )

    def list_locations(self) -> List[Dict[str, Any]]:
        """Return list of all registered locations."""
        results = []
        for loc_id in sorted(self._locations.keys()):
            info = self.get_location(loc_id)
            results.append(info.to_dict())
        return results
