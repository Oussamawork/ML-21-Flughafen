"""Per-gate marker geometry (TDD-04). Each concourse declares a numbering range
and an arm line (hub -> tip) in layout.yaml; gates are spaced evenly along it
(with a small alternating offset to mimic the jetbridge stubs). Lets the map
label every gate A1..D49 and pin a flight's exact gate, airport-agnostic.
"""

from __future__ import annotations

import math
import re


def normalize_gate(gate: str | None) -> str | None:
    """`c030`/`C30`/`c 30` -> `C30`; strips zero-padding so codes match AirLabs."""
    if not gate:
        return None
    m = re.match(r"\s*([A-Za-z]+)\s*0*([0-9]+)", str(gate))
    return f"{m.group(1).upper()}{m.group(2)}" if m else str(gate).strip().upper()


def gate_markers(layout: dict) -> list[dict]:
    """All gate markers for the airport: [{code, x, y}] along each concourse arm."""
    out: list[dict] = []
    for letter, spec in (layout.get("concourse_gates") or {}).items():
        fr, to = int(spec["from"]), int(spec["to"])
        s, e = spec["start"], spec["end"]
        dx, dy = e["x"] - s["x"], e["y"] - s["y"]
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length  # perpendicular unit (stub offset)
        span = (to - fr) or 1
        off = float(spec.get("offset", 1.4))  # small, keeps dots on the pier
        for i, num in enumerate(range(fr, to + 1)):
            t = i / span
            out.append({
                "code": f"{letter}{num}",
                "x": round(s["x"] + dx * t + px * off, 2),
                "y": round(s["y"] + dy * t + py * off, 2),
            })
    return out


def gate_xy(layout: dict, gate: str | None) -> dict | None:
    """Exact {x, y} of a specific gate code (None if it doesn't match a marker)."""
    code = normalize_gate(gate)
    if not code:
        return None
    for m in gate_markers(layout):
        if m["code"] == code:
            return {"x": m["x"], "y": m["y"]}
    return None
