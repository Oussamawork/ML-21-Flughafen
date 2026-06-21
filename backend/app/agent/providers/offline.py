"""Deterministic, key-free LLM provider (default).

Reproduces the agent's tool-calling behavior without any model: classify the intent
(flight / directions / service / faq / smalltalk), drive the matching tool(s), then
compose a templated multilingual answer from the results. This keeps the whole
pipeline runnable offline (the project's hard rule). Hosted providers (openai/groq)
do the same with a real model when a key is wired.
"""

from __future__ import annotations

import re

from ..prompts import (
    compose_directions,
    compose_faq,
    compose_flight_answer,
    compose_service,
    template,
)
from .base import LLMResult, ToolCallReq, ToolSpec

# "sv 624" / "SV-624" -> SV + 624.
_FLIGHT_RE = re.compile(r"\b([A-Z]{2})\s*-?\s*(\d{2,4})\b", re.IGNORECASE)

# Wayfinding / movement cues (ar, ary, fr, en).
_ROUTE_WORDS = (
    "how do i get", "how to get", "get to", "way to", "directions", "navigate",
    "take me", "how far", "how long", "how much left", "left for", "route", "walk",
    "الطريق", "كيفاش نمشي", "نمشي", "وصلني", "اوصل", "بعيد", "قداش باقي",
    "comment aller", "itinéraire", "chemin", "aller à", "loin", "mener",
)

# Service type cues -> canonical service_type (matches services.yaml).
_SERVICE_WORDS = {
    "pharmacy": ("pharmacy", "pharmacie", "صيدلية", "فارماسي"),
    "restroom": ("restroom", "toilet", "toilette", "bathroom", "wc", "مرحاض", "تواليت"),
    "lounge": ("lounge", "salon", "صالة", "لاونج"),
    "restaurant": ("restaurant", "dining", "eat", "food", "manger", "مطعم", "ناكل", "أكل"),
    "coffee": ("coffee", "café", "cafe", "قهوة"),
    "atm": ("atm", "cash machine", "distributeur", "صراف", "فلوس"),
}

# Cues that mark a real question (so non-greetings reach the FAQ tool).
_QUESTION_CUES = (
    "?", "؟", "where", "what", "how", "when", "why", "which", "is ", "are ", "can ",
    "do ", "فين", "أين", "اين", "كيف", "متى", "واش", "اش", "شنو",
    "où", "comment", "quand", "est-ce", "peut",
)


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


def _flight_code(text: str, flight_number: str | None) -> str | None:
    if flight_number:
        return flight_number
    match = _FLIGHT_RE.search(text)
    return (match.group(1) + match.group(2)).upper() if match else None


def _service_type(text: str) -> str | None:
    low = text.lower()
    for canonical, words in _SERVICE_WORDS.items():
        if any(w in low for w in words):
            return canonical
    return None


def _is_route(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in _ROUTE_WORDS)


def _looks_like_question(text: str) -> bool:
    low = text.lower()
    if any(cue in low for cue in _QUESTION_CUES):
        return True
    return len(re.findall(r"\w+", text)) >= 3  # a non-trivial sentence -> try the KB


def _has(tools: list[ToolSpec], name: str) -> bool:
    return any(t.name == name for t in tools)


class OfflineProvider:
    def complete(
        self,
        *,
        messages: list[dict],
        tools: list[ToolSpec],
        language: str,
        airport_id: str,
        flight_number: str | None,
        position: str | None = None,
    ) -> LLMResult:
        text = _latest_user_text(messages)

        # --- compose phase: a tool already ran this turn ---------------------
        directions_res = _latest_tool_result(messages, "directions")
        if directions_res is not None:
            return LLMResult(content=compose_directions(directions_res, language), intent="directions")

        service_res = _latest_tool_result(messages, "find_service")
        if service_res is not None:
            return LLMResult(content=compose_service(service_res, language), intent="find_service")

        faq_res = _latest_tool_result(messages, "faq")
        if faq_res is not None:
            return LLMResult(content=compose_faq(faq_res, language), intent="faq")

        flight_res = _latest_tool_result(messages, "flight_status")
        if flight_res is not None:
            gate = (flight_res or {}).get("gate")
            # A wayfinding turn: chain the gate into a directions lookup.
            if _is_route(text) and gate and _has(tools, "directions"):
                return LLMResult(
                    tool_calls=[ToolCallReq("directions", {"gate": gate, "from_node": position, "airport_id": airport_id})],
                    intent="directions",
                )
            return LLMResult(content=compose_flight_answer(flight_res, language), intent="find_gate")

        # --- planning phase (hop 1): pick the first tool by intent ----------
        code = _flight_code(text, flight_number)

        if _is_route(text):
            if code and _has(tools, "flight_status"):  # resolve the gate first
                return LLMResult(
                    tool_calls=[ToolCallReq("flight_status", {"flight_number": code, "airport_id": airport_id})],
                    intent="directions",
                )
            return LLMResult(content=template("no_route", language), intent="directions")

        service_type = _service_type(text)
        if service_type and _has(tools, "find_service"):
            return LLMResult(
                tool_calls=[ToolCallReq("find_service", {"service_type": service_type, "airport_id": airport_id})],
                intent="find_service",
            )

        if code and _has(tools, "flight_status"):
            return LLMResult(
                tool_calls=[ToolCallReq("flight_status", {"flight_number": code, "airport_id": airport_id})],
                intent="find_gate",
            )

        if _looks_like_question(text) and _has(tools, "faq"):
            return LLMResult(
                tool_calls=[ToolCallReq("faq", {"question": text, "airport_id": airport_id, "lang": language})],
                intent="faq",
            )

        return LLMResult(content=template("fallback", language), intent="smalltalk")
