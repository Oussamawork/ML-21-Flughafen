"""Agent graph state (TDD-02 §3.3)."""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict):
    session_id: str
    airport_id: str
    flight_number: str | None  # typed by the user, NOT parsed from STT (TDD-00)
    position: str | None       # current node in the airport map (TDD-04)
    language: str              # ar | ary | fr | en
    messages: list[dict]       # {role, content} (+ tool results: {role:tool,name,result})
    tool_trace: list[dict]     # ToolCall-shaped: {tool, args, result}
    pending_calls: list[dict]  # tool calls queued by agent_llm for the tools node
    answer: str | None
    intent: str | None
    hops: int                  # MAX_TOOL_HOPS guard
