# evaluation/ — System Evaluation (TDD-08)

Objective, reproducible evaluation of the assistant for the report + demo video.

## Run

```bash
# from the repo root (uses the backend venv for the app imports)
backend/.venv/bin/python evaluation/run_eval.py
```

Writes [`reports/system_eval.md`](reports/system_eval.md) and prints a summary.

## What it measures

Scored **in-process** against the deterministic **offline** agent (`LLM_PROVIDER=offline`),
**mock** flight provider, **keyword** KB retriever and **stub** TTS — so results are
reproducible and need no keys, GPU, or network. The harness forces those modes itself.

- **Comprehension** — intent accuracy, overall + per language (ar/ary/fr/en).
- **Tool correctness** — the expected tool fired.
- **Answer facts** — required values present (gate codes, service names), language-agnostic.
- **Language match** — reply language = the input language (detected, not forced).
- **FAQ retrieval hit-rate** — the right KB topic was retrieved (keyword backend;
  Arabic/Darija recall is weaker than ar/fr/en — the demo uses ChromaDB embeddings, TDD-04).
- **Latency** — agent stage p50/p95 (full STT→agent→TTS is in `/converse`'s `latency_ms`).
- **Robustness** — flight API down, hosted-LLM failure (offline fallback), unknown
  flight, code-mixed input — all must degrade gracefully, never crash.

The **ASR** result (the owned model, WER 108→28.8%) lives in `docs/RESULTS_TDD-01.md`
and is summarized at the top of the report.

## Files

- `datasets/scenarios.yaml` — labeled multilingual scenarios.
- `scorers.py` — pure scoring helpers (unit-testable).
- `run_eval.py` — harness: run → score → write report. Exposes `evaluate()`.
- `reports/system_eval.md` — generated report (committed artifact).

A pytest guard (`backend/tests/test_eval.py`) runs the harness on every test run and
asserts the deterministic axes stay green — so an agent regression fails CI.
