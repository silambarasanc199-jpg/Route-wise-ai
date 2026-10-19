"""External services with explicit failure handling and no fabricated results."""
import asyncio
import time
from urllib.parse import quote
import httpx
from .config import settings

_geo_lock = asyncio.Lock()
_last_geocode_at = 0.0

async def geocode_address(query: str) -> dict:
    """Nominatim lookup, serialized to respect its one-request-per-second policy."""
    global _last_geocode_at
    async with _geo_lock:
        wait = settings.nominatim_min_interval - (time.monotonic() - _last_geocode_at)
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.get(settings.nominatim_url, params={"q": query, "format": "jsonv2", "limit": 1}, headers={"User-Agent": settings.nominatim_user_agent})
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("OpenStreetMap geocoding is temporarily unavailable") from exc
        finally:
            _last_geocode_at = time.monotonic()
    if not data:
        raise LookupError("No matching address was found. Try adding a city or postal code.")
    try:
        return {"latitude": float(data[0]["lat"]), "longitude": float(data[0]["lon"]), "display_name": str(data[0]["display_name"])}
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise RuntimeError("The geocoding service returned an invalid response") from exc

async def optimize_route(coordinates: list[tuple[float, float]]) -> dict:
    """OSRM Trip API TSP estimate. Coordinates use (latitude, longitude)."""
    coords = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coordinates)
    url = f"{settings.osrm_url.rstrip('/')}/trip/v1/driving/{quote(coords, safe=';,.~-')}"
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.get(url, params={"source": "first", "roundtrip": "false", "overview": "full", "geometries": "geojson", "steps": "false"})
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise RuntimeError("The road-routing service is temporarily unavailable") from exc
    if data.get("code") != "Ok" or not data.get("trips"):
        raise LookupError(data.get("message") or "No driving route was returned for these locations")
    trip = data["trips"][0]
    waypoints = data.get("waypoints") or []
    if len(waypoints) != len(coordinates):
        raise RuntimeError("The routing service returned incomplete stop ordering")
    ordered_indexes = sorted(range(len(waypoints)), key=lambda i: waypoints[i].get("waypoint_index", len(waypoints)))
    return {"distance_meters": trip["distance"], "duration_seconds": trip["duration"], "geometry": trip.get("geometry"), "ordered_input_indexes": ordered_indexes, "service": "OSRM public driving profile", "estimated": True, "disclaimer": "Road-network estimate from OSRM; not live traffic, dispatch telemetry, or a guaranteed arrival time."}
