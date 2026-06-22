"""System evaluation harness (TDD-08).

Runs the labeled scenario set against the **deterministic offline agent** (offline
LLM + mock flight provider + keyword KB + stub TTS), scores comprehension / tool
correctness / answer facts / language / FAQ retrieval / latency / robustness, and
writes a Markdown report. Reproducible and key-free — no network, no models.

    cd <repo> && python evaluation/run_eval.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# --- bootstrap: import the backend `app` package + force offline/mock modes ----
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ.update(
    LOAD_STT="false",
    LLM_PROVIDER="offline",
    KB_RETRIEVER="keyword",
    TTS_PROVIDER="stub",
    FLIGHT_API_PROVIDER="mock",
)

import yaml  # noqa: E402

from app.agent import build_langgraph_agent  # noqa: E402
from app.services.flight import FlightUnavailable, MockFlightProvider  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scorers import percentile, score_case, tool_names  # noqa: E402

DATASET = Path(__file__).resolve().parent / "datasets" / "scenarios.yaml"
REPORT = Path(__file__).resolve().parent / "reports" / "system_eval.md"
LANGS = ["en", "fr", "ar", "ary"]


class _DownFlightProvider(MockFlightProvider):
    def get_flight(self, flight_number, airport_id):
        raise FlightUnavailable("provider down")


class _FailingLLM:
    def complete(self, **_kw):
        raise RuntimeError("429 rate_limit_exceeded")


def _agent(flight_provider=None, llm_provider=None):
    return build_langgraph_agent(
        flight_provider=flight_provider or MockFlightProvider(),
        llm_provider=llm_provider,
    )


def _run_scenarios(agent) -> tuple[list[dict], list[float]]:
    scenarios = yaml.safe_load(DATASET.read_text())["scenarios"]
    rows, latencies = [], []
    for sc in scenarios:
        t0 = time.perf_counter()
        reply = agent.run(
            text=sc["text"], language=None, airport_id="AUH", history=[],
            flight_number=sc.get("flight_number"), position=sc.get("position"),
        )
        latencies.append((time.perf_counter() - t0) * 1000)
        rows.append({"sc": sc, "reply": reply, **score_case(reply, sc)})
    return rows, latencies


def _rate(rows: list[dict], axis: str, subset=None) -> tuple[int, int]:
    """(passed, total) over rows whose scenario asserts `axis`."""
    use = [r for r in rows if (subset is None or subset(r))]
    judged = [r for r in use if r["checks"][axis] is not None]
    return sum(1 for r in judged if r["checks"][axis]), len(judged)


def _robustness(rows: list[dict]) -> list[tuple[str, bool]]:
    checks = []
    # Flight API down -> graceful, no crash.
    r = _agent(flight_provider=_DownFlightProvider()).run(
        "where is my gate?", None, "AUH", [], flight_number="SV624")
    checks.append(("Flight API down → graceful answer (no crash)", bool(r.answer)))
    # Hosted LLM failure -> offline fallback still answers with the gate.
    r = _agent(llm_provider=_FailingLLM()).run(
        "where is my gate?", None, "AUH", [], flight_number="SV624")
    checks.append(("LLM provider failure → offline fallback answers", "B12" in r.answer))
    # Unknown flight -> sensible message, no crash.
    r = _agent().run("where is my gate for ZZ999?", None, "AUH", [])
    checks.append(("Unknown flight → graceful 'not found'", bool(r.answer)))
    # Code-mixed (Darija + French) -> still answers.
    r = _agent().run("fin kayna la pharmacie?", None, "AUH", [])
    checks.append(("Code-mixed input → still answers", bool(r.answer)))
    return checks


def _pct(n: int, d: int) -> str:
    return f"{n}/{d} ({round(100 * n / d) if d else 0}%)"


def evaluate() -> dict:
    rows, latencies = _run_scenarios(_agent())
    robustness = _robustness(rows)

    intent = _rate(rows, "intent")
    facts = _rate(rows, "facts")
    lang = _rate(rows, "language")
    tool = _rate(rows, "tool")
    source = _rate(rows, "source")  # FAQ retrieval hit-rate (soft)
    p50, p95 = percentile(latencies, 50), percentile(latencies, 95)

    summary = {
        "n": len(rows),
        "intent_accuracy": intent[0] / intent[1] if intent[1] else 0.0,
        "facts_accuracy": facts[0] / facts[1] if facts[1] else 0.0,
        "language_accuracy": lang[0] / lang[1] if lang[1] else 0.0,
        "tool_accuracy": tool[0] / tool[1] if tool[1] else 0.0,
        "faq_hit_rate": source[0] / source[1] if source[1] else 0.0,
        "latency_ms_p50": p50,
        "latency_ms_p95": p95,
        "robustness_passed": sum(1 for _, ok in robustness if ok),
        "robustness_total": len(robustness),
    }
    _write_report(rows, latencies, robustness, intent, facts, lang, tool, source, p50, p95)
    return summary


def _write_report(rows, latencies, robustness, intent, facts, lang, tool, source, p50, p95):
    from datetime import datetime, timezone

    L = []
    L.append("# System Evaluation — Results (TDD-08)\n")
    L.append(f"_Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} · "
             f"deterministic offline agent + mock flight + keyword KB · "
             f"{len(rows)} scenarios._\n")

    L.append("## 1. ASR — the owned model (TDD-01)\n")
    L.append("| Metric | Base whisper-small | Fine-tuned | Relative ↓ |")
    L.append("|---|---|---|---|")
    L.append("| WER | 108.18% | **28.79%** | 73.4% |")
    L.append("| CER | 63.76% | **9.63%** | 84.9% |")
    L.append("\n(DODa held-out, 1,259 samples — see [`../docs/RESULTS_TDD-01.md`](../docs/RESULTS_TDD-01.md).)\n")

    L.append("## 2. System — comprehension & answers\n")
    L.append("| Axis | Score |")
    L.append("|---|---|")
    L.append(f"| Intent accuracy | {_pct(*intent)} |")
    L.append(f"| Tool correctness | {_pct(*tool)} |")
    L.append(f"| Answer facts (gate/service correct) | {_pct(*facts)} |")
    L.append(f"| Language match | {_pct(*lang)} |")
    L.append(f"| FAQ retrieval hit-rate (keyword backend) | {_pct(*source)} |\n")

    L.append("### Intent accuracy by language\n")
    L.append("| Language | Intent |")
    L.append("|---|---|")
    for lg in LANGS:
        L.append(f"| {lg} | {_pct(*_rate(rows, 'intent', lambda r, lg=lg: r['sc']['lang'] == lg))} |")
    L.append("")

    L.append("## 3. Latency (agent stage, in-process)\n")
    L.append(f"- p50: **{p50} ms** · p95: **{p95} ms** over {len(latencies)} runs.")
    L.append("- Full STT→agent→TTS timings are captured live per request in "
             "`/converse`'s `latency_ms` (TDD-06).\n")

    L.append("## 4. Robustness\n")
    L.append("| Case | Result |")
    L.append("|---|---|")
    for name, ok in robustness:
        L.append(f"| {name} | {'✅ pass' if ok else '❌ fail'} |")
    L.append("")

    L.append("## 5. Per-scenario detail\n")
    L.append("| id | lang | intent | tool | facts | lang | src |")
    L.append("|---|---|---|---|---|---|---|")
    for r in rows:
        c = r["checks"]
        m = lambda v: "·" if v is None else ("✓" if v else "✗")  # noqa: E731
        L.append(f"| {r['sc']['id']} | {r['sc']['lang']} | {m(c['intent'])} | "
                 f"{m(c['tool'])} | {m(c['facts'])} | {m(c['language'])} | {m(c['source'])} |")
    L.append("")
    L.append("> FAQ retrieval uses the dependency-free **keyword** backend here for "
             "reproducibility; Arabic/Darija FAQ recall is weaker than ar/fr/en — the "
             "real demo uses ChromaDB multilingual embeddings (TDD-04). Owned-model "
             "quality is Whisper (§1); RAG is infrastructure.\n")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L))


def main() -> None:
    s = evaluate()
    print("=== System evaluation (TDD-08) ===")
    for k, v in s.items():
        print(f"  {k}: {round(v, 3) if isinstance(v, float) else v}")
    print(f"\nReport written to {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
