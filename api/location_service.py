"""
Location Registry and Spatial Colocation Service.

Resolves requested geographic coordinates to actual NWP forecast grid points,
computes explicit spatial mismatch distance (km), and manages regional groupings.

If actual forecast grid coordinates are not supplied by the source dataset,
actual_grid_coordinates and spatial_distance_km remain unresolved (None).
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

    # Default registered locations (20 Indian candidate stations; 8 core Phase 2 benchmark stations)
    DEFAULT_LOCATIONS: Dict[str, Dict[str, Any]] = {
        # North
        "delhi": {
            "location_id": "delhi",
            "country": "India",
            "state_region": "National Capital Region",
            "city": "Delhi",
            "requested_latitude": 28.6139,
            "requested_longitude": 77.2090,
            "verified_grid_latitude": 28.50,
            "verified_grid_longitude": 77.25,
            "climate_zone": "Cwa/BSh",
            "meteorological_regime": "Subtropical Semi-Arid / Continental",
            "elevation_m": 214.0,
            "is_benchmark": True,
            "rationale": "Extreme seasonal temperature swings, winter radiation fog, pre-monsoon heatwaves, continental landlocked setting.",
        },
        "srinagar": {
            "location_id": "srinagar",
            "country": "India",
            "state_region": "Jammu and Kashmir",
            "city": "Srinagar",
            "requested_latitude": 34.0837,
            "requested_longitude": 74.7973,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Cfb/Dfb",
            "meteorological_regime": "Himalayan Mountain & Valley",
            "elevation_m": 1585.0,
            "is_benchmark": True,
            "rationale": "Complex orographic forcing, alpine cold, winter western disturbances, strong valley temperature inversions.",
        },
        "chandigarh": {
            "location_id": "chandigarh",
            "country": "India",
            "state_region": "Chandigarh",
            "city": "Chandigarh",
            "requested_latitude": 30.7333,
            "requested_longitude": 76.7794,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Cwa",
            "meteorological_regime": "Sub-Himalayan Plains",
            "elevation_m": 321.0,
            "is_benchmark": False,
            "rationale": "Foothill transition zone between Gangetic plains and Siwalik ranges.",
        },
        "jaipur": {
            "location_id": "jaipur",
            "country": "India",
            "state_region": "Rajasthan",
            "city": "Jaipur",
            "requested_latitude": 26.9124,
            "requested_longitude": 75.7873,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "BSh/BWh",
            "meteorological_regime": "Hot Semi-Arid / Desert Margin",
            "elevation_m": 431.0,
            "is_benchmark": True,
            "rationale": "High convective instability, dry boundary layer, dust/aerosol radiative forcing, Thar Desert proximity.",
        },
        "lucknow": {
            "location_id": "lucknow",
            "country": "India",
            "state_region": "Uttar Pradesh",
            "city": "Lucknow",
            "requested_latitude": 26.8467,
            "requested_longitude": 80.9462,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Cwa",
            "meteorological_regime": "Central Gangetic Plains",
            "elevation_m": 123.0,
            "is_benchmark": False,
            "rationale": "Deep alluvial plain, intense monsoon trough passage, dense winter advection fog.",
        },
        # West
        "mumbai": {
            "location_id": "mumbai",
            "country": "India",
            "state_region": "Maharashtra",
            "city": "Mumbai",
            "requested_latitude": 19.0760,
            "requested_longitude": 72.8777,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Am/Aw",
            "meteorological_regime": "Tropical Coastal / Maritime",
            "elevation_m": 14.0,
            "is_benchmark": True,
            "rationale": "Strong marine boundary layer, coastal monsoon precipitation bursts, high humidity, maritime thermal moderation.",
        },
        "pune": {
            "location_id": "pune",
            "country": "India",
            "state_region": "Maharashtra",
            "city": "Pune",
            "requested_latitude": 18.5204,
            "requested_longitude": 73.8567,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "BSh/Aw",
            "meteorological_regime": "Western Ghats Rain-Shadow",
            "elevation_m": 560.0,
            "is_benchmark": False,
            "rationale": "Lee-side orographic drying, plateau climate, sharp rainfall gradient east of Ghats.",
        },
        "ahmedabad": {
            "location_id": "ahmedabad",
            "country": "India",
            "state_region": "Gujarat",
            "city": "Ahmedabad",
            "requested_latitude": 23.0225,
            "requested_longitude": 72.5714,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "BSh",
            "meteorological_regime": "Semi-Arid Western Plains",
            "elevation_m": 53.0,
            "is_benchmark": False,
            "rationale": "Hot semi-arid transitional zone with high summer thermal peaks.",
        },
        "goa": {
            "location_id": "goa",
            "country": "India",
            "state_region": "Goa",
            "city": "Panaji",
            "requested_latitude": 15.2993,
            "requested_longitude": 73.8278,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Am",
            "meteorological_regime": "Konkan Coastal Monsoon",
            "elevation_m": 10.0,
            "is_benchmark": False,
            "rationale": "Direct Arabian Sea monsoon intercept with heavy orographic coastal rainfall.",
        },
        # Central
        "bhopal": {
            "location_id": "bhopal",
            "country": "India",
            "state_region": "Madhya Pradesh",
            "city": "Bhopal",
            "requested_latitude": 23.2599,
            "requested_longitude": 77.4126,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Cwa/Aw",
            "meteorological_regime": "Central Indian Plateau",
            "elevation_m": 527.0,
            "is_benchmark": False,
            "rationale": "Malwa Plateau inland continental climate with distinct seasonal monsoons.",
        },
        "nagpur": {
            "location_id": "nagpur",
            "country": "India",
            "state_region": "Maharashtra",
            "city": "Nagpur",
            "requested_latitude": 21.1458,
            "requested_longitude": 79.0882,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Aw",
            "meteorological_regime": "Deccan Interior Continental",
            "elevation_m": 310.0,
            "is_benchmark": False,
            "rationale": "Geographic center of India with extreme summer continental heating.",
        },
        "raipur": {
            "location_id": "raipur",
            "country": "India",
            "state_region": "Chhattisgarh",
            "city": "Raipur",
            "requested_latitude": 21.2514,
            "requested_longitude": 81.6296,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Aw",
            "meteorological_regime": "Mahanadi Basin Tropical",
            "elevation_m": 298.0,
            "is_benchmark": False,
            "rationale": "Eastern central plateau basin with high summer humidity and convective storm tracks.",
        },
        # East & North-East
        "kolkata": {
            "location_id": "kolkata",
            "country": "India",
            "state_region": "West Bengal",
            "city": "Kolkata",
            "requested_latitude": 22.5726,
            "requested_longitude": 88.3639,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Aw/Cwa",
            "meteorological_regime": "Tropical Wet-and-Dry / Deltaic",
            "elevation_m": 9.0,
            "is_benchmark": True,
            "rationale": "Gangetic delta moisture convergence, severe pre-monsoon thunderstorms (Kalbaishakhi/Nor'westers).",
        },
        "bhubaneswar": {
            "location_id": "bhubaneswar",
            "country": "India",
            "state_region": "Odisha",
            "city": "Bhubaneswar",
            "requested_latitude": 20.2961,
            "requested_longitude": 85.8245,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Aw",
            "meteorological_regime": "Eastern Coastal Plains",
            "elevation_m": 45.0,
            "is_benchmark": False,
            "rationale": "Bay of Bengal coastal plain prone to tropical low-pressure depressions and cyclones.",
        },
        "ranchi": {
            "location_id": "ranchi",
            "country": "India",
            "state_region": "Jharkhand",
            "city": "Ranchi",
            "requested_latitude": 23.3441,
            "requested_longitude": 85.3096,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Cwa",
            "meteorological_regime": "Chota Nagpur Plateau",
            "elevation_m": 651.0,
            "is_benchmark": False,
            "rationale": "Forested plateau elevation providing moderate temperatures and localized convective showers.",
        },
        "guwahati": {
            "location_id": "guwahati",
            "country": "India",
            "state_region": "Assam",
            "city": "Guwahati",
            "requested_latitude": 26.1445,
            "requested_longitude": 91.7362,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Cwa",
            "meteorological_regime": "Subtropical Valley / Monsoonal",
            "elevation_m": 55.0,
            "is_benchmark": True,
            "rationale": "Brahmaputra river valley microclimate, extreme monsoon precipitation volume, persistent orographic cloud cover.",
        },
        # South
        "bengaluru": {
            "location_id": "bengaluru",
            "country": "India",
            "state_region": "Karnataka",
            "city": "Bengaluru",
            "requested_latitude": 12.9716,
            "requested_longitude": 77.5946,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Aw",
            "meteorological_regime": "Elevated Interior Plateau",
            "elevation_m": 920.0,
            "is_benchmark": True,
            "rationale": "High-elevation Deccan plateau, mild diurnal thermal cycle, localized afternoon orographic convection.",
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
            "climate_zone": "As/Aw",
            "meteorological_regime": "Tropical Maritime / Coromandel Coast",
            "elevation_m": 7.0,
            "is_benchmark": True,
            "rationale": "Northeast retreating monsoon dominance, maritime thermal buffering, coastal cyclonic vulnerability.",
        },
        "hyderabad": {
            "location_id": "hyderabad",
            "country": "India",
            "state_region": "Telangana",
            "city": "Hyderabad",
            "requested_latitude": 17.3850,
            "requested_longitude": 78.4867,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "BSh/Aw",
            "meteorological_regime": "Telangana Semi-Arid Plateau",
            "elevation_m": 542.0,
            "is_benchmark": False,
            "rationale": "Inland Deccan plateau with high diurnal temperature variations and seasonal monsoons.",
        },
        "kochi": {
            "location_id": "kochi",
            "country": "India",
            "state_region": "Kerala",
            "city": "Kochi",
            "requested_latitude": 9.9312,
            "requested_longitude": 76.2673,
            "verified_grid_latitude": None,
            "verified_grid_longitude": None,
            "climate_zone": "Am",
            "meteorological_regime": "Malabar Coast Monsoon Gateway",
            "elevation_m": 4.0,
            "is_benchmark": False,
            "rationale": "Southwest monsoon onset gateway with high year-round relative humidity and heavy rainfall.",
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
            climate_zone=cfg.get("climate_zone"),
            meteorological_regime=cfg.get("meteorological_regime"),
            elevation_m=cfg.get("elevation_m"),
            is_benchmark=cfg.get("is_benchmark", False),
            rationale=cfg.get("rationale"),
        )

    def list_locations(self) -> List[Dict[str, Any]]:
        """Return list of all registered locations."""
        results = []
        for loc_id in sorted(self._locations.keys()):
            info = self.get_location(loc_id)
            results.append(info.to_dict())
        return results

    def list_benchmark_locations(self) -> List[Dict[str, Any]]:
        """Return list of the 8 core Phase 2 benchmark locations."""
        results = []
        for loc_id in sorted(self._locations.keys()):
            if self._locations[loc_id].get("is_benchmark", False):
                info = self.get_location(loc_id)
                results.append(info.to_dict())
        return results

    def get_all_location_ids(self) -> List[str]:
        """Return list of all registered location IDs."""
        return sorted(list(self._locations.keys()))

    def get_benchmark_location_ids(self) -> List[str]:
        """Return list of all 8 core benchmark location IDs."""
        return sorted([
            loc_id for loc_id, cfg in self._locations.items()
            if cfg.get("is_benchmark", False)
        ])

    def has_location(self, location_id: str) -> bool:
        """Check if a location_id is currently registered."""
        return location_id.strip().lower() in self._locations

    def register_location(
        self,
        location_id: str,
        requested_latitude: float,
        requested_longitude: float,
        country: str = "India",
        state_region: str = "Custom Region",
        city: Optional[str] = None,
        verified_grid_latitude: Optional[float] = None,
        verified_grid_longitude: Optional[float] = None,
        climate_zone: Optional[str] = None,
        meteorological_regime: Optional[str] = None,
        elevation_m: Optional[float] = None,
        is_benchmark: bool = False,
        rationale: Optional[str] = None,
    ) -> LocationInfo:
        """
        Dynamically register a new monitoring location into the registry at runtime.

        Args:
            location_id: Unique location identifier.
            requested_latitude: Target latitude in degrees [-90, 90].
            requested_longitude: Target longitude in degrees [-180, 180].
            country: Country name.
            state_region: State or administrative region.
            city: City name (defaults to capitalized location_id).
            verified_grid_latitude: Optional verified NWP grid latitude.
            verified_grid_longitude: Optional verified NWP grid longitude.
            climate_zone: Optional Köppen climate zone tag.
            meteorological_regime: Optional physical regime descriptor.
            elevation_m: Optional elevation in meters above sea level.
            is_benchmark: True if part of the scientific benchmark subset.
            rationale: Optional rationale for inclusion.

        Returns:
            LocationInfo dataclass for the newly registered location.
        """
        if not isinstance(location_id, str) or not location_id.strip():
            raise ValueError(f"Invalid location_id '{location_id}'. Must be a non-empty string.")

        loc_key = location_id.strip().lower()

        # Validate coordinate finiteness and physical bounds
        try:
            req_lat_f = float(requested_latitude)
            req_lon_f = float(requested_longitude)
        except (TypeError, ValueError) as err:
            raise ValueError(f"Requested coordinates must be valid numbers: {err}") from err

        if math.isnan(req_lat_f) or math.isinf(req_lat_f) or req_lat_f < -90.0 or req_lat_f > 90.0:
            raise ValueError(f"Invalid requested_latitude: {requested_latitude}. Must be finite and in [-90.0, 90.0].")
        if math.isnan(req_lon_f) or math.isinf(req_lon_f) or req_lon_f < -180.0 or req_lon_f > 180.0:
            raise ValueError(f"Invalid requested_longitude: {requested_longitude}. Must be finite and in [-180.0, 180.0].")

        # Benchmark protection: prevent accidental overwrite of core benchmark locations with differing coordinates
        if self.is_benchmark_location(loc_key):
            existing_cfg = self._locations[loc_key]
            existing_lat = existing_cfg["requested_latitude"]
            existing_lon = existing_cfg["requested_longitude"]
            if not (math.isclose(existing_lat, req_lat_f, abs_tol=1e-4) and math.isclose(existing_lon, req_lon_f, abs_tol=1e-4)):
                raise ValueError(
                    f"Cannot overwrite protected benchmark location '{loc_key}' with differing coordinates "
                    f"(existing: {existing_lat}, {existing_lon}; requested: {req_lat_f}, {req_lon_f})."
                )
            # If coordinates match, idempotent call returns existing location
            return self.get_location(loc_key)

        city_name = city or loc_key.capitalize()

        self._locations[loc_key] = {
            "location_id": loc_key,
            "country": country,
            "state_region": state_region,
            "city": city_name,
            "requested_latitude": req_lat_f,
            "requested_longitude": req_lon_f,
            "verified_grid_latitude": float(verified_grid_latitude) if verified_grid_latitude is not None else None,
            "verified_grid_longitude": float(verified_grid_longitude) if verified_grid_longitude is not None else None,
            "climate_zone": climate_zone,
            "meteorological_regime": meteorological_regime,
            "elevation_m": float(elevation_m) if elevation_m is not None else None,
            "is_benchmark": bool(is_benchmark),
            "rationale": rationale,
        }

        return self.get_location(loc_key)

    def resolve_location(
        self,
        location_id_or_name: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        **kwargs: Any,
    ) -> LocationInfo:
        """
        Resolve a location by ID if registered, or dynamically register it if coordinates are supplied.

        Args:
            location_id_or_name: Location identifier or name.
            latitude: Latitude (required if location is not already registered).
            longitude: Longitude (required if location is not already registered).
            **kwargs: Optional metadata fields passed to register_location.

        Returns:
            LocationInfo dataclass.
        """
        if not isinstance(location_id_or_name, str) or not location_id_or_name.strip():
            raise ValueError(f"Invalid location_id_or_name '{location_id_or_name}'. Must be a non-empty string.")

        loc_key = location_id_or_name.strip().lower()
        if self.has_location(loc_key):
            actual_grid_lat = kwargs.get("actual_grid_lat")
            actual_grid_lon = kwargs.get("actual_grid_lon")
            return self.get_location(loc_key, actual_grid_lat=actual_grid_lat, actual_grid_lon=actual_grid_lon)

        if latitude is not None and longitude is not None:
            return self.register_location(
                location_id=loc_key,
                requested_latitude=latitude,
                requested_longitude=longitude,
                **kwargs,
            )

        raise KeyError(
            f"Location '{location_id_or_name}' is not registered and no coordinates were supplied to register it on-the-fly."
        )

    def is_benchmark_location(self, location_id: str) -> bool:
        """Check if a location belongs to the core Phase 2 benchmark set."""
        loc_key = location_id.strip().lower()
        if loc_key not in self._locations:
            return False
        return bool(self._locations[loc_key].get("is_benchmark", False))

    def get_climate_zone(self, location_id: str) -> Optional[str]:
        """Retrieve the Köppen climate zone descriptor for a registered location."""
        loc_key = location_id.strip().lower()
        if loc_key not in self._locations:
            raise KeyError(f"Unknown location_id '{location_id}'")
        return self._locations[loc_key].get("climate_zone")

    def get_meteorological_regime(self, location_id: str) -> Optional[str]:
        """Retrieve the meteorological regime descriptor for a registered location."""
        loc_key = location_id.strip().lower()
        if loc_key not in self._locations:
            raise KeyError(f"Unknown location_id '{location_id}'")
        return self._locations[loc_key].get("meteorological_regime")

    def get_locations_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Filter registered locations by state_region or broad geographical zone."""
        region_clean = region.strip().lower()
        results = []
        for loc_id, cfg in self._locations.items():
            if region_clean in cfg.get("state_region", "").lower():
                results.append(self.get_location(loc_id).to_dict())
        return results

    def get_locations_by_climate(self, climate_zone: str) -> List[Dict[str, Any]]:
        """Filter registered locations by Köppen climate zone substring."""
        cz_clean = climate_zone.strip().upper()
        results = []
        for loc_id, cfg in self._locations.items():
            cz = cfg.get("climate_zone", "").upper()
            if cz_clean in cz:
                results.append(self.get_location(loc_id).to_dict())
        return results
