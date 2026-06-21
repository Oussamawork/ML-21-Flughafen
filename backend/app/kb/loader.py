"""Load an airport data pack (TDD-04). Airport-agnostic: a pack is just the YAML
under `data/<airport_id>/` — no airport facts live in code. Packs are cached after
first load (they are small and read-only at runtime).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parent / "data"


class AirportNotFound(Exception):
    """No data pack exists for the requested airport_id."""


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass
class Pack:
    """A parsed, ready-to-query airport data pack."""

    airport_id: str
    airport: dict
    layout: dict
    services: list[dict]
    checkin: dict
    faq: list[dict]
    # node -> [(neighbour, distance_m)], expanded from layout.edges (symmetric).
    adjacency: dict[str, list[tuple[str, int]]] = field(default_factory=dict)

    @property
    def positions(self) -> dict[str, dict]:
        return self.layout.get("positions", {})

    @property
    def node_names(self) -> dict[str, str]:
        return self.layout.get("nodes", {})

    def gate_node(self, gate: str | None) -> str | None:
        if not gate:
            return None
        return self.layout.get("gate_nodes", {}).get(gate.upper())

    def baggage_node(self, baggage: str | None) -> str | None:
        if not baggage:
            return None
        return self.layout.get("baggage_nodes", {}).get(str(baggage))


def _build_adjacency(layout: dict) -> dict[str, list[tuple[str, int]]]:
    adj: dict[str, list[tuple[str, int]]] = {n: [] for n in layout.get("nodes", {})}
    for edge in layout.get("edges", []):
        a, b, d = edge["a"], edge["b"], int(edge.get("distance_m", 95))
        adj.setdefault(a, []).append((b, d))
        adj.setdefault(b, []).append((a, d))
    return adj


@lru_cache(maxsize=8)
def load_pack(airport_id: str) -> Pack:
    """Load + cache the data pack for `airport_id` (case-insensitive)."""
    aid = airport_id.upper()
    base = DATA_DIR / aid
    if not base.is_dir():
        raise AirportNotFound(aid)
    layout = _read(base / "layout.yaml")
    return Pack(
        airport_id=aid,
        airport=_read(base / "airport.yaml"),
        layout=layout,
        services=_read(base / "services.yaml").get("services", []),
        checkin=_read(base / "checkin.yaml"),
        faq=_read(base / "faq.yaml").get("faq", []),
        adjacency=_build_adjacency(layout),
    )


def available_airports() -> list[str]:
    """Airport ids that have a data pack (used by /airports later)."""
    if not DATA_DIR.is_dir():
        return []
    return sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir())
