"""LangGraphAgent — adapts the compiled graph to the backend `Agent` Protocol."""

from __future__ import annotations

from ..services.agent import AgentReply
from ..services.lang import detect_language
from .graph import build_graph
from .providers.base import LLMProvider
from .tools import Tool


class LangGraphAgent:
    def __init__(self, graph, registry: dict[str, Tool], max_hops: int) -> None:
        self._graph = graph
        self._registry = registry
        self._max_hops = max_hops

    def run(
        self,
        text: str,
        language: str | None,
        airport_id: str,
        history: list[dict],
        *,
        flight_number: str | None = None,
        position: str | None = None,
    ) -> AgentReply:
        state = {
            "session_id": "",
            "airport_id": airport_id,
            "flight_number": flight_number,
            "position": position,
            "language": language or detect_language(text),
            "messages": [*history, {"role": "user", "content": text}],
            "tool_trace": [],
            "pending_calls": [],
            "answer": None,
            "intent": None,
            "hops": 0,
        }
        final = self._graph.invoke(state)
        return AgentReply(
            answer=final.get("answer") or "",
            language=final["language"],
            intent=final.get("intent") or "smalltalk",
            tool_trace=final.get("tool_trace", []),
        )
