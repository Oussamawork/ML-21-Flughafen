"""Tests for the flight-data tool (TDD-03) — mock provider + AirLabs normalization.

No network: the AirLabs adapter is exercised with a stubbed `_fetch`, so the suite
never calls the live API or touches the 1,000/month quota.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import flight as flight_mod
from app.services.flight import (
    AirLabsProvider,
    FlightUnavailable,
    MockFlightProvider,
    build_flight_provider,
    normalize_flight_number,
)

# A trimmed real-shape AirLabs /flight response object (departing AUH).
AIRLABS_RESP = {
    "flight_iata": "SV624", "airline_iata": "SV", "status": "scheduled",
    "dep_iata": "AUH", "dep_terminal": "A", "dep_gate": "B12",
    "dep_time": "2026-06-21 18:55", "dep_estimated": "2026-06-21 18:55",
    "dep_delayed": None, "arr_iata": "RUH", "arr_terminal": "1",
    "arr_gate": "12", "arr_baggage": "5", "aircraft_icao": "A320",
}


def test_normalize_flight_number():
    assert normalize_flight_number("sv 624") == "SV624"
    assert normalize_flight_number("SV-624") == "SV624"


def test_mock_provider_known_and_unknown():
    p = MockFlightProvider()
    info = p.get_flight("sv624", "AUH")
    assert info and info["gate"] == "B12" and info["source"] == "mock"
    assert p.get_flight("ZZ999", "AUH") is None
    assert p.get_flight("SV624", "CMN") is None  # airport-scoped, nothing for CMN


def test_airlabs_departure_scoping(monkeypatch):
    p = AirLabsProvider("fake-key")
    monkeypatch.setattr(p, "_fetch", lambda code: AIRLABS_RESP)
    info = p.get_flight("SV624", "AUH")
    assert info["direction"] == "departure"
    assert info["terminal"] == "A" and info["gate"] == "B12"
    assert info["baggage"] is None  # departures have no baggage belt
    assert info["scheduled"] == "2026-06-21 18:55" and info["source"] == "airlabs"


def test_airlabs_arrival_scoping(monkeypatch):
    p = AirLabsProvider("fake-key")
    monkeypatch.setattr(p, "_fetch", lambda code: AIRLABS_RESP)
    info = p.get_flight("SV624", "RUH")  # AUH->RUH, scope to arrival
    assert info["direction"] == "arrival"
    assert info["terminal"] == "1" and info["gate"] == "12"
    assert info["baggage"] == "5"  # arrivals carry the belt


def test_airlabs_caches(monkeypatch):
    p = AirLabsProvider("fake-key", ttl=60)
    calls = {"n": 0}

    def fetch(code):
        calls["n"] += 1
        return AIRLABS_RESP

    monkeypatch.setattr(p, "_fetch", fetch)
    p.get_flight("SV624", "AUH")
    p.get_flight("SV624", "AUH")
    assert calls["n"] == 1  # second call served from cache


def test_airlabs_unavailable_propagates(monkeypatch):
    p = AirLabsProvider("fake-key")

    def boom(code):
        raise FlightUnavailable("month_limit_exceeded")

    monkeypatch.setattr(p, "_fetch", boom)
    with pytest.raises(FlightUnavailable):
        p.get_flight("SV624", "AUH")


def test_build_provider_requires_key_for_airlabs(monkeypatch):
    monkeypatch.setattr(settings, "flight_api_provider", "airlabs")
    monkeypatch.setattr(settings, "airlabs_api_key", "")
    with pytest.raises(RuntimeError):
        build_flight_provider()


# --- endpoint (uses the default mock provider) ---

def test_flight_endpoint_found():
    with TestClient(app) as c:
        r = c.post("/flight", json={"flight_number": "SV624"})
    assert r.status_code == 200
    body = r.json()
    assert body["flight"]["gate"] == "B12"
    assert body["flight"]["direction"] == "departure"
    # KB map (TDD-04) now enriches the flight with a route to the gate + check-in.
    assert body["route"]["route"][-1] == "gate-b12"
    assert body["route"]["route_summary"]["distance_m"] > 0
    assert "Saudia" in body["checkin"]["zone"]


def test_flight_endpoint_not_found():
    with TestClient(app) as c:
        r = c.post("/flight", json={"flight_number": "ZZ999"})
    assert r.status_code == 404


def test_flight_endpoint_503_on_provider_error(monkeypatch):
    monkeypatch.setattr(
        flight_mod.MockFlightProvider,
        "get_flight",
        lambda self, n, a: (_ for _ in ()).throw(FlightUnavailable("down")),
    )
    with TestClient(app) as c:
        r = c.post("/flight", json={"flight_number": "SV624"})
    assert r.status_code == 503
