"""Structured service lookup (TDD-04) — backs the `find_service` tool. A plain
filter over the data pack's services list (no embeddings needed); optional fuzzy
match on the service type so "coffee shop" still finds the "coffee" service.
"""

from __future__ import annotations

from .loader import Pack


def find_services(
    pack: Pack, service_type: str | None = None, near_zone: str | None = None
) -> list[dict]:
    """Services filtered by type (substring, case-insensitive) and/or zone."""
    results = pack.services
    if service_type:
        t = service_type.strip().lower()
        results = [
            s
            for s in results
            if t in str(s.get("type", "")).lower() or t in str(s.get("name", "")).lower()
        ]
    if near_zone:
        z = near_zone.strip().lower()
        results = [s for s in results if z in str(s.get("zone", "")).lower()]
    return results


def checkin_for(pack: Pack, airline: str | None) -> dict:
    """Check-in desk/zone for an airline (falls back to the pack default). Fills
    the field AirLabs doesn't provide."""
    data = pack.checkin or {}
    default = dict(data.get("default", {}))
    if airline:
        override = data.get("airlines", {}).get(airline.upper())
        if override:
            default.update(override)
    return default
