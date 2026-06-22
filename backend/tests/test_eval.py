"""Guard: the TDD-08 evaluation harness runs and its deterministic axes stay green.

Doubles as a regression net — if an agent change breaks intent routing, grounding,
or robustness, this fails. Language/FAQ-hit are reported but not gated (FAQ keyword
recall for ar/ary is a known soft spot; see evaluation/README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[2] / "evaluation"
sys.path.insert(0, str(EVAL_DIR))

import run_eval  # noqa: E402


def test_evaluation_harness_axes_hold():
    s = run_eval.evaluate()
    assert s["n"] >= 20
    assert s["intent_accuracy"] >= 0.95          # routing is deterministic
    assert s["facts_accuracy"] >= 0.95           # grounded gate/service facts
    assert s["tool_accuracy"] >= 0.95            # right tool fired
    assert s["robustness_passed"] == s["robustness_total"]  # never crashes
    assert (EVAL_DIR / "reports" / "system_eval.md").exists()
