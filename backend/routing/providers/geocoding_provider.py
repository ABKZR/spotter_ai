from __future__ import annotations

import logging
import httpx
from django.conf import settings

from routing.domain.models import Coordinate, Location
from routing.providers.base import GeocodingProvider

logger = logging.getLogger(__name__)

_ORS_URL = "https://api.openrouteservice.org/geocode"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org"
_TIMEOUT = 8.0

# Major North American logistics corridors and metro hubs
MAJOR_HUBS: list[tuple[str, float, float]] = [
    ("Los Angeles, CA, USA", 34.0522, -118.2437),
    ("Dallas, TX, USA", 32.7767, -96.7970),
    ("Chicago, IL, USA", 41.8781, -87.6298),
    ("Houston, TX, USA", 29.7604, -95.3698),
    ("Phoenix, AZ, USA", 33.4484, -112.0740),
    ("Philadelphia, PA, USA", 39.9526, -75.1652),
    ("San Antonio, TX, USA", 29.4241, -98.4936),
    ("San Diego, CA, USA", 32.7157, -117.1611),
    ("Detroit, MI, USA", 42.3314, -83.0458),
    ("Indianapolis, IN, USA", 39.7684, -86.1581),
    ("Columbus, OH, USA", 39.9612, -82.9988),
    ("Charlotte, NC, USA", 35.2271, -80.8431),
    ("Seattle, WA, USA", 47.6062, -122.3321),
    ("Denver, CO, USA", 39.7392, -104.9903),
    ("Nashville, TN, USA", 36.1627, -86.7816),
    ("Atlanta, GA, USA", 33.7490, -84.3880),
    ("Memphis, TN, USA", 35.1495, -90.0490),
    ("Kansas City, MO, USA", 39.0997, -94.5786),
    ("Miami, FL, USA", 25.7617, -80.1918),
    ("New York, NY, USA", 40.7128, -74.0060),
    ("Boston, MA, USA", 42.3601, -71.0589),
    ("Las Vegas, NV, USA", 36.1699, -115.1398),
    ("Minneapolis, MN, USA", 44.9778, -93.2650),
    ("St. Louis, MO, USA", 38.6270, -90.1994),
    ("Cleveland, OH, USA", 41.4993, -81.6944),
    ("Cincinnati, OH, USA", 39.1031, -84.5120),
    ("Pittsburgh, PA, USA", 40.4406, -79.9959),
    ("Tampa, FL, USA", 27.9506, -82.4572),
    ("Orlando, FL, USA", 28.5383, -81.3792),
    ("Salt Lake City, UT, USA", 40.7608, -111.8910),
    ("Oklahoma City, OK, USA", 35.4676, -97.5164),
    ("Louisville, KY, USA", 38.2527, -85.7585),
    ("Baltimore, MD, USA", 39.2904, -76.6122),
    ("Milwaukee, WI, USA", 43.0389, -87.9065),
    ("Albuquerque, NM, USA", 35.0844, -106.6504),
    ("New Orleans, LA, USA", 29.9511, -90.0715),
    ("Omaha, NE, USA", 41.2565, -95.9345),
    ("Birmingham, AL, USA", 33.5186, -86.8104),
    ("Portland, OR, USA", 45.5152, -122.6784),
    ("San Francisco, CA, USA", 37.7749, -122.4194),
    ("Austin, TX, USA", 30.2672, -97.7431),
    ("El Paso, TX, USA", 31.7619, -106.4850),
    ("Toronto, ON, Canada", 43.6532, -79.3832),
    ("Montreal, QC, Canada", 45.5017, -73.5673),
    ("Vancouver, BC, Canada", 49.2827, -123.1207),
    ("Calgary, AB, Canada", 51.0447, -114.0719),
]


class ORSGeocodingProvider(GeocodingProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or getattr(settings, "ORS_API_KEY", "")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self._api_key,
            "Accept": "application/json",
            "User-Agent": "SpotterAI-TruckRouting/1.0",
        }

    async def geocode(self, address: str) -> Location:
        addr_clean = address.strip()
        addr_lower = addr_clean.lower()

        for label, lat, lon in MAJOR_HUBS:
            city_name = label.split(",")[0].lower()
            if addr_lower == city_name or addr_lower.startswith(city_name):
                return Location(label=label, coordinate=Coordinate(lat, lon))

        if self._api_key:
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(
                        f"{_ORS_URL}/search",
                        params={"text": addr_clean, "size": 1, "boundary.country": "USA,CAN"},
                        headers=self._headers(),
                    )
                    if resp.status_code == 200:
                        features = resp.json().get("features", [])
                        if features:
                            coords = features[0]["geometry"]["coordinates"]
                            lbl = features[0]["properties"].get("label", addr_clean)
                            return Location(
                                label=lbl,
                                coordinate=Coordinate(latitude=coords[1], longitude=coords[0]),
                            )
            except Exception as exc:
                logger.warning("ORS geocoding failed: %s", exc)

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    f"{_NOMINATIM_URL}/search",
                    params={
                        "q": addr_clean,
                        "format": "json",
                        "limit": 1,
                        "countrycodes": "us,ca",
                    },
                    headers={"User-Agent": "SpotterAI-TruckRouting/1.0"},
                )
                if resp.status_code == 200:
                    items = resp.json()
                    if items:
                        item = items[0]
                        return Location(
                            label=item.get("display_name", addr_clean),
                            coordinate=Coordinate(
                                latitude=float(item["lat"]),
                                longitude=float(item["lon"]),
                            ),
                        )
        except Exception as exc:
            logger.error("Nominatim geocode failed: %s", exc)

        for label, lat, lon in MAJOR_HUBS:
            if any(term in label.lower() for term in addr_lower.split(",")):
                return Location(label=label, coordinate=Coordinate(lat, lon))

        raise ValueError(
            f"Could not resolve a North American road location for '{address}'. Please specify city and state (e.g. 'Dallas, TX')."
        )

    async def autocomplete(self, query: str) -> list[dict]:
        q = query.strip().lower()
        if len(q) < 2:
            return []

        results: list[dict] = []
        seen_labels: set[str] = set()

        for label, lat, lon in MAJOR_HUBS:
            if q in label.lower():
                results.append({"label": label, "latitude": lat, "longitude": lon})
                seen_labels.add(label.lower())
                if len(results) >= 5:
                    return results

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"{_NOMINATIM_URL}/search",
                    params={
                        "q": query.strip(),
                        "format": "json",
                        "limit": 5,
                        "countrycodes": "us,ca",
                    },
                    headers={"User-Agent": "SpotterAI-TruckRouting/1.0"},
                )
                if resp.status_code == 200:
                    for item in resp.json():
                        lbl = item.get("display_name", "")
                        if any(term in lbl.lower() for term in ["provincial park", "national park", "nature reserve", "wilderness"]):
                            continue
                        if lbl.lower() not in seen_labels:
                            results.append(
                                {
                                    "label": lbl,
                                    "latitude": float(item["lat"]),
                                    "longitude": float(item["lon"]),
                                }
                            )
                            seen_labels.add(lbl.lower())
        except Exception as exc:
            logger.debug("Nominatim autocomplete failed: %s", exc)

        return results[:5]
