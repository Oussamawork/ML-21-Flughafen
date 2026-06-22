"""Pure scoring helpers for the system evaluation (TDD-08). No I/O, no app
imports — just functions over an agent reply + a scenario spec, so they're trivial
to unit-test and reason about.
"""

from __future__ import annotations


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile (p in 0..100). 0 for an empty list."""
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(p / 100 * (len(ordered) - 1))))
    return round(ordered[k], 1)


def tool_names(tool_trace: list[dict]) -> list[str]:
    return [t.get("tool") for t in tool_trace]


def sources(tool_trace: list[dict]) -> list[str]:
    out: list[str] = []
    for t in tool_trace:
        result = t.get("result") or {}
        out.extend(result.get("sources", []) or [])
    return out


def contains_all(answer: str, needles: list[str]) -> bool:
    low = (answer or "").lower()
    return all(n.lower() in low for n in needles)


def score_case(reply, scenario: dict) -> dict:
    """Score one reply against a scenario. Each axis is None when the scenario
    doesn't assert it, else True/False. `ok` is the AND of asserted axes."""
    checks: dict[str, bool | None] = {
        "intent": None,
        "tool": None,
        "facts": None,
        "language": None,
        "source": None,
    }
    if "expect_intent" in scenario:
        checks["intent"] = reply.intent == scenario["expect_intent"]
    if "expect_tool" in scenario:
        checks["tool"] = scenario["expect_tool"] in tool_names(reply.tool_trace)
    if "expect_contains" in scenario:
        checks["facts"] = contains_all(reply.answer, scenario["expect_contains"])
    if "expect_lang" in scenario:
        checks["language"] = reply.language == scenario["expect_lang"]
    if "expect_source" in scenario:
        checks["source"] = any(scenario["expect_source"] in s for s in sources(reply.tool_trace))

    asserted = [v for v in checks.values() if v is not None]
    return {"checks": checks, "ok": all(asserted) if asserted else True}
