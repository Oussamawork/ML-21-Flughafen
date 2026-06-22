"""LangGraph agent package (TDD-02). Built once and shared (see state.py)."""

from __future__ import annotations

from ..config import settings
from ..kb import KnowledgeBase, build_knowledge_base
from ..services.flight import FlightProvider, build_flight_provider
from .agent import LangGraphAgent
from .graph import build_graph
from .providers import LLMProvider, build_llm_provider
from .tools import build_tool_registry

__all__ = ["LangGraphAgent", "build_langgraph_agent"]


def build_langgraph_agent(
    flight_provider: FlightProvider | None = None,
    llm_provider: LLMProvider | None = None,
    knowledge_base: KnowledgeBase | None = None,
    max_hops: int | None = None,
) -> LangGraphAgent:
    flight_provider = flight_provider or build_flight_provider()
    llm_provider = llm_provider or build_llm_provider()
    knowledge_base = knowledge_base or build_knowledge_base()
    max_hops = settings.max_tool_hops if max_hops is None else max_hops
    registry = build_tool_registry(flight_provider, knowledge_base)
    graph = build_graph(llm_provider, registry, max_hops, fallback=_build_fallback())
    return LangGraphAgent(graph, registry, max_hops)


def _build_fallback() -> LLMProvider:
    """Fallback chain for when the primary hosted LLM fails: Groq (if keyed and not
    already the primary), then the deterministic offline brain. So a hosted outage
    degrades to Groq, then offline — the turn never crashes (TDD-00 §6)."""
    from .providers import FallbackProvider, build_llm_provider as _build
    from .providers.offline import OfflineProvider

    chain: list[LLMProvider] = []
    if (
        settings.llm_provider not in ("offline", "groq")
        and settings.groq_api_key
    ):
        try:
            chain.append(_build("groq"))
        except Exception:  # SDK/key issue -> just skip to offline
            pass
    chain.append(OfflineProvider())
    return chain[0] if len(chain) == 1 else FallbackProvider(chain)
