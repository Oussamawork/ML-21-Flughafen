"""Knowledge-base tools (TDD-03 §3.1) wrapping the KnowledgeBase (app/kb).

`directions` runs map-graph pathfinding, `find_service` filters the service index,
`faq` does RAG over the airport FAQ. Typed args in, plain JSON dicts out; only
`ToolUnavailable`/`ToolBadInput` cross the boundary (the graph catches them).
"""

from __future__ import annotations

from ...config import settings
from ...kb import AirportNotFound, KnowledgeBase
from . import ToolBadInput, ToolUnavailable

DIRECTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "to_node": {"type": "string", "description": "Target layout node, e.g. concourse-c, duty-free, baggage"},
        "gate": {"type": "string", "description": "Gate code, e.g. C33 (resolved to its concourse)"},
        "from_node": {"type": "string", "description": "Origin node; omit to use the passenger position or entrance"},
        "airport_id": {"type": "string", "default": "AUH"},
    },
}

FIND_SERVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "service_type": {"type": "string", "description": "pharmacy|restroom|lounge|food|atm|..."},
        "near_zone": {"type": "string"},
        "airport_id": {"type": "string", "default": "AUH"},
    },
    "required": ["service_type"],
}

FAQ_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string", "description": "Free-text airport question"},
        "airport_id": {"type": "string", "default": "AUH"},
    },
    "required": ["question"],
}


# airport_id defaults to the configured airport — a hosted LLM may omit the
# optional arg even though each tool's schema lists it.
def directions(
    kb: KnowledgeBase,
    airport_id: str | None = None,
    to_node: str | None = None,
    gate: str | None = None,
    from_node: str | None = None,
) -> dict:
    airport_id = airport_id or settings.default_airport_id
    try:
        return kb.directions(airport_id, to_node=to_node, gate=gate, from_node=from_node)
    except AirportNotFound as exc:
        raise ToolUnavailable(f"no knowledge base for airport {exc}") from exc


def find_service(
    kb: KnowledgeBase,
    airport_id: str | None = None,
    service_type: str | None = None,
    near_zone: str | None = None,
) -> dict:
    airport_id = airport_id or settings.default_airport_id
    try:
        return kb.find_service(airport_id, service_type, near_zone)
    except AirportNotFound as exc:
        raise ToolUnavailable(f"no knowledge base for airport {exc}") from exc


def faq(kb: KnowledgeBase, airport_id: str | None = None, question: str | None = None, lang: str | None = None) -> dict:
    if not question:
        raise ToolBadInput("faq requires a question")
    airport_id = airport_id or settings.default_airport_id
    try:
        return kb.faq(airport_id, question, lang=lang)
    except AirportNotFound as exc:
        raise ToolUnavailable(f"no knowledge base for airport {exc}") from exc
