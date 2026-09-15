"""Small geocoding helper used by job forms.

The public Nominatim service is suitable for development/testing at low volume.
Production deployments should configure a dedicated geocoding provider and API key.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.conf import settings


@dataclass(frozen=True)
class GeocodingResult:
    latitude: float
    longitude: float
    display_name: str = ""


# Offline/dev fallback for the locations included in the seeded demo and filters.
CITY_FALLBACKS = {
    ("santa maria", "ca"): (34.9530, -120.4357),
    ("san luis obispo", "ca"): (35.2828, -120.6596),
    ("san jose", "ca"): (37.3382, -121.8863),
}
ZIP_FALLBACKS = {
    "93454": (34.9530, -120.4357),
    "93455": (34.8653, -120.4168),
    "93458": (34.9630, -120.4579),
    "93401": (35.2828, -120.6596),
    "95112": (37.3541, -121.8847),
}


def geocode_job_location(*, address: str = "", city: str = "", state: str = "", zip_code: str = "") -> GeocodingResult | None:
    """Resolve a job address, falling back to city/state or ZIP when needed."""
    address = (address or "").strip()
    city = (city or "").strip()
    state = (state or "").strip()
    zip_code = (zip_code or "").strip()

    # When only a known city/ZIP is supplied, use the built-in development data
    # immediately. A street address still receives a full provider lookup first.
    if not address and zip_code in ZIP_FALLBACKS:
        lat, lon = ZIP_FALLBACKS[zip_code]
        return GeocodingResult(lat, lon, f"{zip_code}, USA")
    key = (city.lower(), state.lower())
    if not address and key in CITY_FALLBACKS:
        lat, lon = CITY_FALLBACKS[key]
        return GeocodingResult(lat, lon, f"{city}, {state}")

    queries = []
    full = ", ".join(part for part in [address, city, state, zip_code, "USA"] if part)
    if full:
        queries.append(full)
    city_query = ", ".join(part for part in [city, state, "USA"] if part)
    if city_query and city_query not in queries:
        queries.append(city_query)
    if zip_code:
        queries.append(f"{zip_code}, USA")

    endpoint = getattr(settings, "GEOCODING_URL", "https://nominatim.openstreetmap.org/search")
    user_agent = getattr(settings, "GEOCODING_USER_AGENT", "CareerConnect-Development/1.0")
    timeout = getattr(settings, "GEOCODING_TIMEOUT", 4)

    for query in queries:
        params = urlencode({"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "us"})
        request = Request(f"{endpoint}?{params}", headers={"User-Agent": user_agent, "Accept": "application/json"})
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload:
                return GeocodingResult(float(payload[0]["lat"]), float(payload[0]["lon"]), payload[0].get("display_name", ""))
        except (URLError, HTTPError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
            continue

    if zip_code in ZIP_FALLBACKS:
        lat, lon = ZIP_FALLBACKS[zip_code]
        return GeocodingResult(lat, lon, f"{zip_code}, USA")
    key = (city.lower(), state.lower())
    if key in CITY_FALLBACKS:
        lat, lon = CITY_FALLBACKS[key]
        return GeocodingResult(lat, lon, f"{city}, {state}")
    return None
