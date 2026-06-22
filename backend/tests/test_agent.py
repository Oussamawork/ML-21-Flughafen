"""Unit tests for the LangGraph agent (TDD-02), offline + mock flight provider.

No network, no LLM key: the OfflineProvider is deterministic and the flight tool
uses MockFlightProvider. Build agents directly to inject providers.
"""

from __future__ import annotations

import sys

import pytest

from app.agent import build_langgraph_agent
from app.agent.providers.base import LLMResult, ToolCallReq
from app.schemas import ToolCall
from app.services.flight import FlightUnavailable, MockFlightProvider


def make_agent(flight_provider=None, llm_provider=None, max_hops=4):
    return build_langgraph_agent(
        flight_provider=flight_provider or MockFlightProvider(),
        llm_provider=llm_provider,
        max_hops=max_hops,
    )


def test_flight_code_calls_tool_and_answers():
    reply = make_agent().run("where is my gate for flight SV-624?", None, "AUH", [])
    assert reply.intent == "find_gate"
    assert "B12" in reply.answer
    call = reply.tool_trace[0]
    assert call["tool"] == "flight_status"
    assert call["args"]["flight_number"] == "SV624"
    assert call["result"]["gate"] == "B12"


def test_typed_flight_number_used_without_code_in_text():
    # The dashboard passes the typed number; the question need not repeat it.
    reply = make_agent().run("where is my gate?", "en", "AUH", [], flight_number="EK201")
    assert reply.tool_trace[0]["args"]["flight_number"] == "EK201"
    assert "A7" in reply.answer


def test_unknown_flight():
    reply = make_agent().run("status of flight ZZ999", None, "AUH", [])
    assert reply.intent == "find_gate"
    assert reply.tool_trace[0]["result"] == {}
    assert "couldn't find" in reply.answer.lower()


def test_no_flight_code_falls_back():
    reply = make_agent().run("hello there", None, "AUH", [])
    assert reply.intent == "smalltalk"
    assert reply.tool_trace == []


@pytest.mark.parametrize(
    "text,lang",
    [
        ("أين بوابتي للرحلة SV624", "ar"),
        ("où est ma porte pour le vol SV624", "fr"),
        ("where is my gate for SV624", "en"),
    ],
)
def test_language_matrix(text, lang):
    reply = make_agent().run(text, None, "AUH", [])
    assert reply.language == lang


class _AlwaysToolProvider:
    """A fake LLM that never stops asking for a tool — exercises the hop guard."""

    def complete(self, **_kw) -> LLMResult:
        return LLMResult(tool_calls=[ToolCallReq("flight_status", {"flight_number": "SV624", "airport_id": "AUH"})], intent="find_gate")


def test_max_tool_hops_guard():
    agent = make_agent(llm_provider=_AlwaysToolProvider(), max_hops=2)
    reply = agent.run("loop please", "en", "AUH", [])
    assert len(reply.tool_trace) <= 2
    assert reply.answer  # still produced an answer (compose fallback)


class _DownProvider(MockFlightProvider):
    def get_flight(self, flight_number, airport_id):
        raise FlightUnavailable("provider down")


def test_flight_unavailable_degrades_gracefully():
    reply = make_agent(flight_provider=_DownProvider()).run(
        "gate for SV624", "en", "AUH", []
    )
    assert reply.tool_trace[0]["result"] == {"error": "provider down"}
    assert reply.answer  # graceful, no exception


def test_tool_trace_shape_constructs_toolcall():
    reply = make_agent().run("gate for SV624", "en", "AUH", [])
    for tc in reply.tool_trace:
        assert set(tc) == {"tool", "args", "result"}
        ToolCall(**tc)  # the route layer does this; must not raise


def test_default_agent_imports_no_llm_sdk():
    # The offline default must not pull in any hosted SDK (no network / no key).
    make_agent()
    assert "openai" not in sys.modules
    assert "groq" not in sys.modules
    assert "anthropic" not in sys.modules


def test_fallback_provider_tries_in_order():
    from app.agent.providers.base import LLMResult
    from app.agent.providers.fallback import FallbackProvider

    class _Boom:
        def complete(self, **_kw):
            raise RuntimeError("down")

    class _Ok:
        def complete(self, **_kw):
            return LLMResult(content="ok", intent="smalltalk")

    fp = FallbackProvider([_Boom(), _Ok()])
    out = fp.complete(messages=[], tools=[], language="en", airport_id="AUH", flight_number=None)
    assert out.content == "ok"


# --- KB tools (TDD-04) -----------------------------------------------------

def test_directions_chains_flight_then_route():
    # "how do I get to my gate?" -> flight_status (gate) -> directions (route).
    reply = make_agent().run("how do I get to my gate?", "en", "AUH", [], flight_number="SV624")
    assert reply.intent == "directions"
    assert [t["tool"] for t in reply.tool_trace] == ["flight_status", "directions"]
    assert reply.tool_trace[-1]["result"]["route"][-1] == "concourse-b"
    assert "Concourse B" in reply.answer


def test_find_service_tool():
    reply = make_agent().run("where is the pharmacy?", "en", "AUH", [])
    assert reply.intent == "find_service"
    assert reply.tool_trace[0]["tool"] == "find_service"
    assert "Airport Pharmacy" in reply.answer


def test_faq_tool():
    reply = make_agent().run("I lost my luggage, what do I do?", "en", "AUH", [])
    assert reply.intent == "faq"
    assert reply.tool_trace[0]["tool"] == "faq"
    assert "baggage" in reply.answer.lower()


def test_tools_default_airport_id_when_omitted():
    # A hosted LLM may omit the optional airport_id arg; tools must not crash.
    from app.agent.tools import flight_tools, kb_tools
    from app.kb import build_knowledge_base

    kb = build_knowledge_base()
    assert flight_tools.find_gate(MockFlightProvider(), "SV624")["gate"] == "B12"
    assert flight_tools.flight_status(MockFlightProvider(), "SV624")["gate"] == "B12"
    assert kb_tools.directions(kb, gate="B12")["route"][-1] == "concourse-b"
    assert "results" in kb_tools.find_service(kb, service_type="pharmacy")
    assert "answer" in kb_tools.faq(kb, question="lost baggage")


class _FailingProvider:
    """A hosted LLM that always errors (e.g. rate limit / outage)."""

    def complete(self, **_kw):
        raise RuntimeError("429 rate_limit_exceeded")


def test_llm_provider_failure_degrades_to_offline():
    # A Groq/OpenAI outage must not 500 the turn — it falls back to the offline
    # brain, which still resolves the typed flight via tools.
    agent = make_agent(llm_provider=_FailingProvider())
    reply = agent.run("where is my gate?", "en", "AUH", [], flight_number="SV624")
    assert reply.answer  # graceful, no exception
    assert "B12" in reply.answer  # offline fallback still drove the flight tool


def test_directions_without_target_is_graceful():
    reply = make_agent().run("how do I get there?", "en", "AUH", [])
    assert reply.intent == "directions"
    assert reply.tool_trace == []  # no flight/gate to resolve -> no_route message
    assert reply.answer
