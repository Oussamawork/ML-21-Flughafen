"""Flight tools (TDD-03 §3.1) wrapping the FlightProvider (services/flight.py).

`flight_status` returns the full canonical dict; `find_gate` is the gate/terminal
subset. Both raise `ToolUnavailable` on provider quota/network errors so the graph
can degrade gracefully.
"""

from __future__ import annotations

from ...services.flight import (
    FlightProvider,
    FlightUnavailable,
    normalize_flight_number,
)
from . import ToolUnavailable

FLIGHT_STATUS_SCHEMA = {
    "type": "object",
    "properties": {
        "flight_number": {"type": "string", "description": "IATA code, e.g. SV624"},
        "airport_id": {"type": "string", "default": "AUH"},
    },
    "required": ["flight_number"],
}

FIND_GATE_SCHEMA = FLIGHT_STATUS_SCHEMA


def flight_status(provider: FlightProvider, flight_number: str, airport_id: str) -> dict:
    """Live status/gate/terminal/times for a flight. `{}` if not found."""
    code = normalize_flight_number(flight_number)
    try:
        info = provider.get_flight(code, airport_id)
    except FlightUnavailable as exc:
        raise ToolUnavailable(str(exc)) from exc
    return info or {}


def find_gate(provider: FlightProvider, flight_number: str, airport_id: str) -> dict:
    """Gate + terminal subset of flight_status."""
    info = flight_status(provider, flight_number, airport_id)
    if not info:
        return {}
    return {
        "flight_number": info.get("flight_number"),
        "gate": info.get("gate"),
        "terminal": info.get("terminal"),
        "status": info.get("status"),
    }
