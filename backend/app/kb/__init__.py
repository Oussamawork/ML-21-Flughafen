"""Airport Knowledge Base (TDD-04) — the facade the agent tools and /map call.

Wraps the data-pack loader, the map-graph pathfinder, the structured service index,
and the RAG retriever behind one airport-agnostic object. Built once and shared
(see state.py), exactly like the flight provider.
"""

from __future__ import annotations

from . import graph
from .loader import AirportNotFound, Pack, available_airports, load_pack
from .retriever import Retriever, build_retriever
from .services_index import checkin_for, find_services

__all__ = ["KnowledgeBase", "build_knowledge_base", "AirportNotFound", "available_airports"]


class KnowledgeBase:
    def __init__(self, retriever: Retriever) -> None:
        self._retriever = retriever

    def pack(self, airport_id: str) -> Pack:
        return load_pack(airport_id)  # raises AirportNotFound for an unknown airport

    # --- map / directions (graph) -----------------------------------------
    def layout(self, airport_id: str) -> dict:
        """Nodes + positions + zones for the frontend map (no route)."""
        pack = load_pack(airport_id)
        return {
            "nodes": pack.node_names,
            "positions": pack.positions,
            "zones": pack.layout.get("zones", []),
        }

    def directions(
        self,
        airport_id: str,
        *,
        to_node: str | None = None,
        gate: str | None = None,
        from_node: str | None = None,
    ) -> dict:
        """Route to `to_node` (or to the node for a `gate` code). Origin defaults
        to the passenger's `from_node`, else the pack's default origin."""
        pack = load_pack(airport_id)
        default = pack.airport.get("default_origin") or "entrance"
        # Target: an explicit node if it's real, else resolve the gate code.
        target = to_node if (to_node and to_node in pack.node_names) else pack.gate_node(gate)
        if not target or target not in pack.node_names:
            return {"route": [], "steps": [], "positions": {}, "route_summary": None,
                    "from_node": from_node or default, "to_node": None}
        # Origin: the passenger's node if valid, else the default. Never route a
        # node to itself (a hosted LLM sometimes sets origin == destination).
        origin = from_node if (from_node and from_node in pack.node_names) else default
        if origin == target:
            origin = default if default != target else target
        return graph.directions(pack, origin, target)

    # --- services (structured) --------------------------------------------
    def find_service(
        self, airport_id: str, service_type: str | None = None, near_zone: str | None = None
    ) -> dict:
        pack = load_pack(airport_id)
        return {"results": find_services(pack, service_type, near_zone)}

    def checkin(self, airport_id: str, airline: str | None = None) -> dict:
        return checkin_for(load_pack(airport_id), airline)

    # --- faq (RAG) ---------------------------------------------------------
    def faq(self, airport_id: str, question: str, lang: str | None = None) -> dict:
        chunks = self._retriever.retrieve(
            question, airport_id, k=3, type_filter="faq", lang=lang
        )
        if not chunks:
            return {"answer": None, "sources": []}
        return {
            "answer": chunks[0].text,
            "lang": chunks[0].lang,
            "sources": [c.source for c in chunks],
        }


def build_knowledge_base(retriever: Retriever | None = None) -> KnowledgeBase:
    return KnowledgeBase(retriever or build_retriever())
