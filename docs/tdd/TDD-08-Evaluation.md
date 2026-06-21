# TDD-08 — Evaluation & Testing

**Component:** `evaluation/`
**Status:** ⚪ Not started
**Depends on:** all components · **Feeds:** report + demo video

---

## 1. Purpose

Measure the system objectively, per the proposal's evaluation requirement, and
produce the tables/figures for the report and video.

## 2. Requirements satisfied

- *Evaluation of system performance: comprehension accuracy, response latency,
  answer quality.*
- *Experimental evaluation* + *test scenarios* (rubric).

## 3. Evaluation axes

### 3.1 ASR (the owned model) — primary ML result
- **WER / CER** on a held-out Darija/Arabic test set.
- **Base vs. fine-tuned** comparison table (the headline number).
- Tooling: `asr_finetuning/src/evaluate_model.py` (TDD-01).

**Result (2026-06-21, `Amassu/whisper-small-darija`, DODa held-out, 1,259 samples):**

| Metric | Base whisper-small | Fine-tuned | Relative ↓ |
|---|---|---|---|
| WER | 108.18% | **28.79%** | 73.4% |
| CER | 63.76% | **9.63%** | 84.9% |

Full write-up + qualitative before/after: [`../RESULTS_TDD-01.md`](../RESULTS_TDD-01.md).

### 3.2 Comprehension / intent accuracy
- Curated test set of ~50–100 passenger utterances (ar/ary/fr/en) labeled with
  expected intent + key entities (flight number, service type).
- Metrics: intent accuracy, entity extraction accuracy (exact match on flight no.).

### 3.3 Answer quality
- Scenario suite (golden Q→expected-fact). Automatic checks where deterministic
  (e.g. correct gate returned given a mocked flight). 
- Human/LLM-as-judge rubric (1–5) for fluency, correctness, language-match, on a
  sample — documented methodology, small N is fine for a master project.

### 3.4 Latency
- Per-stage timing (STT / agent / TTS / total) captured by the backend (TDD-06),
  aggregated to p50/p95 over the scenario runs.

### 3.5 Robustness
- Flight API down → graceful degradation works.
- Wrong/unknown flight number → sensible response.
- Code-mixed input (Darija + French) → still answers.

## 4. Test scenarios (examples)

| # | Input (lang) | Expected |
|---|---|---|
| S1 | "ayna bawwabati, rihlati SV-624" (ar) | gate/terminal for SV624, in Arabic |
| S2 | "Où est la pharmacie la plus proche ?" (fr) | nearest pharmacy, in French |
| S3 | "Is flight EK201 delayed?" (en) | delay status, in English |
| S4 | "fin kayn lounge?" (ary) | lounge location, answer understandable |
| S5 | flight API offline | apologetic fallback, no crash |

## 5. Deliverables / artifacts

- `evaluation/datasets/` — utterance + scenario test sets.
- `evaluation/run_eval.py` — runs scenarios against the API, collects metrics.
- `evaluation/reports/` — generated tables (WER, intent acc, latency p50/p95).

## 6. Dependencies

`jiwer`/`evaluate` (ASR), `pytest` (scenario harness), `pandas`/`matplotlib`
(tables/plots), the running backend (or component mocks).

## 7. Open questions / risks

- **Labeled Darija eval data** scarcity → may hand-label a small set ourselves.
- **Answer-quality subjectivity** → fix a rubric + report N and judges.
- **Live-data variability** → use mocked flight provider for reproducible scoring.

## 8. Task checklist

- [ ] ASR base-vs-FT WER/CER table
- [ ] Intent/entity test set + scorer
- [ ] Scenario harness `run_eval.py` against the API
- [ ] Latency aggregation (p50/p95)
- [ ] Robustness cases
- [ ] Generate report tables/plots
