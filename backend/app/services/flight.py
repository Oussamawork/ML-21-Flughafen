"""Flight-data service (TDD-03 integration point).

Interface: `get_flight(flight_number, airport_id) -> dict | None`.

- `MockFlightProvider` (default): canned flights, no network/key — so the API and
  tests run offline and never touch the AirLabs 1,000/month quota.
- `AirLabsProvider`: real AirLabs v9 lookup by flight number, normalized to the
  canonical schema, scoped to `airport_id`, with a short TTL cache. The API key is
  read from `settings` (server-side only); the AirLabs `request`/meta block (which
  echoes the key) is never propagated — we use `response` only.

Canonical normalized dict (see TDD-03 §3.1):
    flight_number, airline, status, direction (departure|arrival|other),
    scheduled, estimated, actual, gate, terminal, baggage, delay_minutes,
    departure_airport, arrival_airport, aircraft, source
"""

from __future__ import annotations

import re
import time
from typing import Protocol

from ..config import settings


class FlightUnavailable(Exception):
    """Raised on network/quota errors so the agent can degrade gracefully."""


def normalize_flight_number(raw: str) -> str:
    """`sv 624` / `SV-624` -> `SV624` (AirLabs `flight_iata`)."""
    return re.sub(r"[\s\-]+", "", raw).upper()


def _scope(resp: dict, airport_id: str) -> str:
    """Which leg of the flight touches `airport_id`."""
    if resp.get("dep_iata") == airport_id:
        return "departure"
    if resp.get("arr_iata") == airport_id:
        return "arrival"
    return "other"


def _normalize(resp: dict, airport_id: str) -> dict:
    """Map an AirLabs `/flight` response object to the canonical schema."""
    direction = _scope(resp, airport_id)
    dep = direction != "arrival"  # departure or other -> show departure side
    pfx = "dep" if dep else "arr"
    return {
        "flight_number": resp.get("flight_iata") or resp.get("flight_icao"),
        "airline": resp.get("airline_iata"),
        "status": resp.get("status"),
        "direction": direction,
        "scheduled": resp.get(f"{pfx}_time"),
        "estimated": resp.get(f"{pfx}_estimated"),
        "actual": resp.get(f"{pfx}_actual"),
        "terminal": resp.get(f"{pfx}_terminal"),
        "gate": resp.get(f"{pfx}_gate"),
        "baggage": resp.get("arr_baggage") if not dep else None,  # arrivals only
        "delay_minutes": resp.get(f"{pfx}_delayed"),
        "departure_airport": resp.get("dep_iata"),
        "arrival_airport": resp.get("arr_iata"),
        "aircraft": resp.get("aircraft_icao"),
        "source": "airlabs",
    }


class FlightProvider(Protocol):
    def get_flight(self, flight_number: str, airport_id: str) -> dict | None: ...


class AirLabsProvider:
    """Adapter over AirLabs v9 (`GET /flight?flight_iata=...`)."""

    _BASE = "https://airlabs.co/api/v9/flight"

    def __init__(self, api_key: str, ttl: int = 60) -> None:
        if not api_key:
            raise RuntimeError("AIRLABS_API_KEY is required for the airlabs provider.")
        self._key = api_key
        self._ttl = ttl
        self._cache: dict[str, tuple[float, dict | None]] = {}

    def _fetch(self, flight_iata: str) -> dict | None:
        import json
        import urllib.error
        import urllib.parse
        import urllib.request

        url = f"{self._BASE}?" + urllib.parse.urlencode(
            {"flight_iata": flight_iata, "api_key": self._key}
        )
        # AirLabs rejects the default urllib User-Agent with 403; set an explicit one.
        request = urllib.request.Request(url, headers={"User-Agent": "ML-21-Flughafen/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=10) as r:
                data = json.loads(r.read())
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise FlightUnavailable(str(exc)) from exc
        # AirLabs returns 200 with an `error` block on quota/auth failures.
        if isinstance(data, dict) and data.get("error"):
            raise FlightUnavailable(str(data["error"]))
        return (data or {}).get("response") or None  # never propagate `request`/meta

    def get_flight(self, flight_number: str, airport_id: str) -> dict | None:
        code = normalize_flight_number(flight_number)
        key = f"{code}@{airport_id}"
        now = time.time()
        hit = self._cache.get(key)
        if hit and now - hit[0] < self._ttl:
            return hit[1]
        resp = self._fetch(code)
        info = _normalize(resp, airport_id) if resp else None
        self._cache[key] = (now, info)
        return info


# --- MOCK flight data (dev/offline only) -----------------------------------
# Keyed by airport_id so nothing is hard-coded to one airport (TDD-00 rule).
_MOCK: dict[str, dict[str, dict]] = {
    "AUH": {
        "SV624": {
            "flight_number": "SV624", "airline": "SV", "status": "scheduled",
            "direction": "departure", "scheduled": "2026-06-21 18:55",
            "estimated": "2026-06-21 18:55", "actual": None,
            "terminal": "A", "gate": "B12", "baggage": None, "delay_minutes": None,
            "departure_airport": "AUH", "arrival_airport": "RUH",
            "aircraft": "A320", "source": "mock",
        },
        "EK201": {
            "flight_number": "EK201", "airline": "EK", "status": "active",
            "direction": "departure", "scheduled": "2026-06-21 09:40",
            "estimated": "2026-06-21 10:20", "actual": None,
            "terminal": "A", "gate": "A7", "baggage": None, "delay_minutes": 40,
            "departure_airport": "AUH", "arrival_airport": "JFK",
            "aircraft": "B77W", "source": "mock",
        },
    }
}


class MockFlightProvider:
    def get_flight(self, flight_number: str, airport_id: str) -> dict | None:
        code = normalize_flight_number(flight_number)
        return _MOCK.get(airport_id, {}).get(code)


def build_flight_provider() -> FlightProvider:
    if settings.flight_api_provider == "airlabs":
        return AirLabsProvider(settings.airlabs_api_key, ttl=settings.flight_cache_ttl)
    return MockFlightProvider()
