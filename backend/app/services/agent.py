"""LLM agent service (TDD-02/03/04 integration point).

Interface: `run(text, language, airport_id, history) -> AgentReply`.

`StubAgent` is a rule-based placeholder: it detects intent with simple patterns,
calls a **mock** flight tool, and templates an answer in the user's language so
the rest of the pipeline (and the frontend) can be built and demoed now. The real
LangGraph agent (TDD-02) with real tools (TDD-03) and RAG (TDD-04) replaces this
behind the same `run()` signature.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

from .lang import detect_language

_FLIGHT_RE = re.compile(r"\b([A-Z]{2})\s*-?\s*(\d{2,4})\b", re.IGNORECASE)

# --- MOCK airport/flight data (dev only) -----------------------------------
# Keyed by airport_id so nothing is hard-coded to one airport (TDD-00 rule).
# Replaced by the real flight API (TDD-03) + knowledge base (TDD-04).
_MOCK_FLIGHTS: dict[str, dict[str, dict]] = {
    "AUH": {
        "SV624": {
            "gate": "B12",
            "terminal": "T1",
            "boarding": "14:35",
            "status": "on time",
        },
        "EK201": {
            "gate": "A7",
            "terminal": "T3",
            "boarding": "—",
            "status": "delayed 40 min",
        },
    }
}

# Minimal answer templates per detected language.
_TEMPLATES = {
    "gate": {
        "ar": "بوابتك هي {gate}، المبنى {terminal}. وقت الصعود {boarding}.",
        "ary": "البّاب ديالك هو {gate}، تيرمينال {terminal}. البوردينغ {boarding}.",
        "fr": "Votre porte est {gate}, terminal {terminal}. Embarquement à {boarding}.",
        "en": "Your gate is {gate}, terminal {terminal}. Boarding at {boarding}.",
    },
    "unknown_flight": {
        "ar": "لم أجد معلومات عن هذه الرحلة. تأكد من رقم الرحلة من فضلك.",
        "ary": "مالقيتش معلومات على هاد الرحلة. عافاك تأكد من الرقم.",
        "fr": "Je n'ai pas trouvé ce vol. Vérifiez le numéro, s'il vous plaît.",
        "en": "I couldn't find that flight. Please check the flight number.",
    },
    "fallback": {
        "ar": "أنا مساعد المطار. يمكنني مساعدتك في البوابات والرحلات والخدمات.",
        "ary": "أنا مساعد ديال المطار. نقدر نعاونك فالبيبان والرحلات والخدمات.",
        "fr": "Je suis l'assistant de l'aéroport. Je peux aider pour les portes, vols et services.",
        "en": "I'm the airport assistant. I can help with gates, flights and services.",
    },
}


@dataclass
class AgentReply:
    answer: str
    language: str
    intent: str
    tool_trace: list[dict] = field(default_factory=list)


class Agent(Protocol):
    def run(
        self,
        text: str,
        language: str | None,
        airport_id: str,
        history: list[dict],
        *,
        flight_number: str | None = None,
        position: str | None = None,
    ) -> AgentReply: ...


class StubAgent:
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
        lang = language or detect_language(text)
        tmpl = lambda key: _TEMPLATES[key].get(lang, _TEMPLATES[key]["en"])  # noqa: E731

        match = _FLIGHT_RE.search(text)
        if match:
            flight = (match.group(1) + match.group(2)).upper()
            info = _MOCK_FLIGHTS.get(airport_id, {}).get(flight)
            tool_call = {
                "tool": "flight_status",
                "args": {"flight_number": flight, "airport_id": airport_id},
                "result": info,
            }
            if info:
                answer = tmpl("gate").format(**info)
                return AgentReply(answer, lang, "find_gate", [tool_call])
            return AgentReply(tmpl("unknown_flight"), lang, "find_gate", [tool_call])

        return AgentReply(tmpl("fallback"), lang, "smalltalk", [])


def build_agent(flight_provider=None, knowledge_base=None) -> Agent:
    """Pick the agent backend. LangGraph is always used unless AGENT_BACKEND is
    explicitly set to "stub" — so an unset/typo'd value never silently downgrades."""
    from ..config import settings

    if settings.agent_backend == "stub":
        return StubAgent()
    from ..agent import build_langgraph_agent  # lazy: pulls in langgraph

    return build_langgraph_agent(
        flight_provider=flight_provider, knowledge_base=knowledge_base
    )
