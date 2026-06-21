"""Tool registry: maps tool names to (json_schema, callable) for the agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ...services.flight import FlightProvider
from . import flight_tools


@dataclass
class Tool:
    name: str
    json_schema: dict
    fn: Callable[..., dict]  # called as fn(flight_number=..., airport_id=...)


def build_tool_registry(flight_provider: FlightProvider) -> dict[str, Tool]:
    """v1 catalogue = flight tools (TDD-03). KB tools land with TDD-04."""
    return {
        "flight_status": Tool(
            "flight_status",
            flight_tools.FLIGHT_STATUS_SCHEMA,
            lambda **kw: flight_tools.flight_status(flight_provider, **kw),
        ),
        "find_gate": Tool(
            "find_gate",
            flight_tools.FIND_GATE_SCHEMA,
            lambda **kw: flight_tools.find_gate(flight_provider, **kw),
        ),
    }
