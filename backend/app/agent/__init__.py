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
    # Offline fallback so a hosted-LLM failure (rate limit/outage) degrades to the
    # deterministic brain instead of crashing the turn. Cheap, key-free, no network.
    from .providers.offline import OfflineProvider

    fallback = OfflineProvider()
    graph = build_graph(llm_provider, registry, max_hops, fallback=fallback)
    return LangGraphAgent(graph, registry, max_hops)
