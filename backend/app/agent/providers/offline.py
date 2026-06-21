"""Deterministic, key-free LLM provider (default).

Reproduces the agent's tool-calling behavior without any model: detect a flight
code, request `flight_status`, then compose a templated multilingual answer. This
keeps the whole pipeline runnable offline (the project's hard rule).
"""

from __future__ import annotations

import re

from ..prompts import compose_flight_answer, template
from .base import LLMResult, ToolCallReq, ToolSpec

# Same shape as the legacy stub: "sv 624" / "SV-624" -> SV + 624.
_FLIGHT_RE = re.compile(r"\b([A-Z]{2})\s*-?\s*(\d{2,4})\b", re.IGNORECASE)


def _latest_user_text(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content") or ""
    return ""


def _latest_tool_result(messages: list[dict], tool: str) -> dict | None:
    for msg in reversed(messages):
        if msg.get("role") == "tool" and msg.get("name") == tool:
            return msg.get("result")
    return None


class OfflineProvider:
    def complete(
        self,
        *,
        messages: list[dict],
        tools: list[ToolSpec],
        language: str,
        airport_id: str,
        flight_number: str | None,
    ) -> LLMResult:
        # Hop 2: a flight lookup already ran -> compose the final answer.
        result = _latest_tool_result(messages, "flight_status")
        if result is not None:
            return LLMResult(
                content=compose_flight_answer(result, language),
                intent="find_gate",
            )

        # Hop 1: resolve the flight code (typed field wins over text extraction).
        code = flight_number
        if not code:
            match = _FLIGHT_RE.search(_latest_user_text(messages))
            if match:
                code = (match.group(1) + match.group(2)).upper()

        if code and any(t.name == "flight_status" for t in tools):
            return LLMResult(
                tool_calls=[
                    ToolCallReq(
                        "flight_status",
                        {"flight_number": code, "airport_id": airport_id},
                    )
                ],
                intent="find_gate",
            )

        return LLMResult(content=template("fallback", language), intent="smalltalk")
