"""Tool registry: maps tool names to (json_schema, callable) for the agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ...kb import KnowledgeBase
from ...services.flight import FlightProvider
from . import flight_tools, kb_tools


@dataclass
class Tool:
    name: str
    json_schema: dict
    fn: Callable[..., dict]  # called as fn(**args) with the tool-call arguments


def build_tool_registry(
    flight_provider: FlightProvider, kb: KnowledgeBase
) -> dict[str, Tool]:
    """Full catalogue: flight tools (TDD-03) + KB tools (TDD-04)."""
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
        "directions": Tool(
            "directions",
            kb_tools.DIRECTIONS_SCHEMA,
            lambda **kw: kb_tools.directions(kb, **kw),
        ),
        "find_service": Tool(
            "find_service",
            kb_tools.FIND_SERVICE_SCHEMA,
            lambda **kw: kb_tools.find_service(kb, **kw),
        ),
        "faq": Tool(
            "faq",
            kb_tools.FAQ_SCHEMA,
            lambda **kw: kb_tools.faq(kb, **kw),
        ),
    }
