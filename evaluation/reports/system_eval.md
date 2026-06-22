# System Evaluation — Results (TDD-08)

_Generated 2026-06-22 00:53 UTC · deterministic offline agent + mock flight + keyword KB · 27 scenarios._

## 1. ASR — the owned model (TDD-01)

| Metric | Base whisper-small | Fine-tuned | Relative ↓ |
|---|---|---|---|
| WER | 108.18% | **28.79%** | 73.4% |
| CER | 63.76% | **9.63%** | 84.9% |

(DODa held-out, 1,259 samples — see [`../docs/RESULTS_TDD-01.md`](../docs/RESULTS_TDD-01.md).)

## 2. System — comprehension & answers

| Axis | Score |
|---|---|
| Intent accuracy | 27/27 (100%) |
| Tool correctness | 8/8 (100%) |
| Answer facts (gate/service correct) | 17/17 (100%) |
| Language match | 24/27 (89%) |
| FAQ retrieval hit-rate (keyword backend) | 5/5 (100%) |

### Intent accuracy by language

| Language | Intent |
|---|---|
| en | 15/15 (100%) |
| fr | 5/5 (100%) |
| ar | 4/4 (100%) |
| ary | 3/3 (100%) |

## 3. Latency (agent stage, in-process)

- p50: **0.7 ms** · p95: **0.9 ms** over 27 runs.
- Full STT→agent→TTS timings are captured live per request in `/converse`'s `latency_ms` (TDD-06).

## 4. Robustness

| Case | Result |
|---|---|
| Flight API down → graceful answer (no crash) | ✅ pass |
| LLM provider failure → offline fallback answers | ✅ pass |
| Unknown flight → graceful 'not found' | ✅ pass |
| Code-mixed input → still answers | ✅ pass |

## 5. Per-scenario detail

| id | lang | intent | tool | facts | lang | src |
|---|---|---|---|---|---|---|
| gate-en | en | ✓ | ✓ | ✓ | ✓ | · |
| gate-fr | fr | ✓ | · | ✓ | ✓ | · |
| gate-ar | ar | ✓ | · | ✓ | ✓ | · |
| gate-ary | ary | ✓ | · | ✓ | ✗ | · |
| gate-code-en | en | ✓ | · | ✓ | ✓ | · |
| gate-code-text | en | ✓ | · | ✓ | ✓ | · |
| dir-en | en | ✓ | ✓ | ✓ | ✓ | · |
| dir-fr | fr | ✓ | ✓ | ✓ | ✓ | · |
| dir-ar | ar | ✓ | ✓ | ✓ | ✓ | · |
| dir-ary | ary | ✓ | ✓ | ✓ | ✗ | · |
| dir-pos | en | ✓ | ✓ | ✓ | ✓ | · |
| svc-pharm-en | en | ✓ | ✓ | ✓ | ✓ | · |
| svc-pharm-fr | fr | ✓ | · | ✓ | ✓ | · |
| svc-pharm-ar | ar | ✓ | · | ✓ | ✓ | · |
| svc-lounge-en | en | ✓ | · | ✓ | ✓ | · |
| svc-coffee-en | en | ✓ | · | ✓ | ✓ | · |
| svc-restroom-en | en | ✓ | · | ✓ | ✓ | · |
| faq-baggage-en | en | ✓ | ✓ | · | ✓ | ✓ |
| faq-prayer-en | en | ✓ | · | · | ✓ | ✓ |
| faq-connect-en | en | ✓ | · | · | ✓ | ✓ |
| faq-checkin-en | en | ✓ | · | · | ✓ | ✓ |
| faq-baggage-fr | fr | ✓ | · | · | ✓ | ✓ |
| faq-prayer-ar | ar | ✓ | · | · | ✓ | · |
| faq-baggage-ary | ary | ✓ | · | · | ✗ | · |
| hello-en | en | ✓ | · | · | ✓ | · |
| hello-fr | fr | ✓ | · | · | ✓ | · |
| thanks-en | en | ✓ | · | · | ✓ | · |

> FAQ retrieval uses the dependency-free **keyword** backend here for reproducibility; Arabic/Darija FAQ recall is weaker than ar/fr/en — the real demo uses ChromaDB multilingual embeddings (TDD-04). Owned-model quality is Whisper (§1); RAG is infrastructure.
