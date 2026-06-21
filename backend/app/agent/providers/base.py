"""LLM provider interface (TDD-02 §3.1).

One tool-calling method, `complete`, called once per graph hop. It returns either
tool calls (run them and loop) or final content (done). This maps onto OpenAI/Groq
chat-with-tools APIs and lets the offline provider fake the same two-phase shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ToolSpec:
    name: str
    json_schema: dict


@dataclass
class ToolCallReq:
    tool: str
    args: dict
    id: str | None = None  # provider-native tool_call id (for hosted LLM protocol)


@dataclass
class LLMResult:
    content: str | None = None          # final answer when no more tools needed
    tool_calls: list[ToolCallReq] = field(default_factory=list)
    intent: str | None = None


class LLMProvider(Protocol):
    def complete(
        self,
        *,
        messages: list[dict],
        tools: list[ToolSpec],
        language: str,
        airport_id: str,
        flight_number: str | None,
        position: str | None = None,
    ) -> LLMResult: ...
