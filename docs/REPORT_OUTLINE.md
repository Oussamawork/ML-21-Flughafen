# Final Report Outline — Multilingual Smart Airport Wayfinding Assistant

Outline for the written master's report. Grounded in the supervisor's three graded
pillars — **multilingual Moroccan context (ar/ary/fr, code-mixed)**, a **real API
service**, and an **owned/fine-tuned model on your own data** — and mapped to the
project's TDDs (`docs/tdd/`), artifacts, and measured results.

> **Grading map (quick reference):**
> §4 = owned model + dataset construction · §5 = real API service ·
> §1/2/8 = multilingual context · §6 = test scenarios + experimental evaluation ·
> §3/5/7 = architecture, implementation, environment setup.
> The report also feeds the **PPTX** (condense §1/4/6) and the **7-min video**
> (demo = §5.6 + live §6 robustness).

---

## Front matter
- Title, authors, supervisors (A. Mahmoudi; co: S. Frihi, Y. Lehmiani), Master IT 2025–2026.
- **Abstract** (½ page): problem, the fine-tuned Darija/Arabic Whisper as the ML
  contribution, the agentic API system, headline result (**WER 108→28.8%**), key findings.
- Table of contents · list of figures/tables · acronyms (ASR, WER/CER, RAG, STT/TTS, LLM).

## 1. Introduction
- **Context & motivation** — multilingual airport wayfinding in a Moroccan-multilingual
  setting (Arabic/Darija/French, code-mixed); case study Zayed International (AUH).
- **Problem statement** — passengers ask informal/voice questions across languages;
  need structured, grounded guidance (gates, services, directions).
- **Domain note** — the pivot from the pharmacy brief to airport wayfinding (cleared
  with the supervisor); the three general goals still apply.
- **Objectives & contributions** — (i) fine-tuned Darija/Arabic ASR on an own-prepared
  split; (ii) agentic, grounded, multilingual assistant; (iii) a real, deployable
  API + UI; (iv) reproducible evaluation. State explicitly what is *owned ML* vs
  *infrastructure*.
- **Report structure**.

## 2. Background & Related Work
- **Multilingual ASR & Darija** — Whisper; low-resource Darija; why generic SaaS speech
  APIs fall short on Darija (motivates fine-tuning). Cite the DODa dataset.
- **Multilingual NLP / code-mixing**, intent understanding, language ID.
- **Retrieval-Augmented Generation (RAG)** and **tool-using LLM agents** (LangGraph).
- **TTS** for Arabic/French; airport wayfinding / indoor routing.
- Positioning: what we adopt vs. build.

## 3. System Design & Architecture (from TDD-00)
- End-to-end pipeline diagram: **Frontend → FastAPI → STT (Whisper) → LLM agent
  (LangGraph) → tools (AirLabs) / RAG (ChromaDB) → TTS → response**.
- **Cross-cutting design principles** (graded-relevant): *language is first-class*
  (`ar/ary/fr/en` across boundaries), *airport-agnostic* (data keyed by `airport_id`),
  *typed flight number not parsed from audio* ("identity over inference"), *secrets
  server-side only*.
- Component contracts + request/response data model.

## 4. Dataset & ASR Model — the owned ML contribution (TDD-01) ⭐ *grade-critical*
- **Dataset preparation** (explicitly graded): DODa (`atlasia/DODa-audio-dataset`,
  ~9h46m); Arabic-script column; **sentence-grouped train/eval split to prevent
  leakage**; null-row filtering; CPU/no-FFmpeg audio loading fixes.
- **Model & fine-tuning** — `openai/whisper-small`, `Seq2SeqTrainer`, hyperparameters,
  3000 steps on a T4; serving interface (`WhisperTranscriber`).
- **Results** — base vs fine-tuned: **WER 108.18→28.79% (−73.4%), CER 63.76→9.63%
  (−84.9%)** on 1,259 held-out samples; qualitative before/after (base emits wrong
  scripts on Darija). Model card; pushed to `Amassu/whisper-small-darija`.
  See `docs/RESULTS_TDD-01.md` + `asr_finetuning/MODEL_CARD.md`.
- *Make this the longest, most rigorous chapter — it's the core ML deliverable.*

## 5. Implementation — the API system (TDD-02–07)
- **5.1 Backend API (TDD-06)** — FastAPI; endpoints (`/transcribe /chat /converse
  /speak /flight /map /airports`, WS); session state; swappable services behind
  interfaces with offline stubs; per-stage `latency_ms`.
- **5.2 LLM agent (TDD-02)** — LangGraph graph `detect_lang → agent_llm → tools* →
  compose`, `MAX_TOOL_HOPS`; **LLM behind a provider interface** (offline-deterministic
  default / Groq / OpenAI); graceful degradation (LLM failure → offline brain).
- **5.3 Tools & flight data (TDD-03)** — AirLabs integration (gate/terminal/status;
  free-tier caching; **API key stripped server-side**); KB tools
  `directions`/`find_service`/`faq`.
- **5.4 Knowledge base & RAG (TDD-04)** — per-`airport_id` YAML packs; **map-graph BFS
  routing**; **ChromaDB + multilingual-e5** FAQ retrieval with a dependency-free
  keyword fallback; ingestion pipeline.
- **5.5 TTS (TDD-05)** — local **MMS-TTS** neural voices (ar/fr/en; Darija→Arabic),
  on-CPU, no key.
- **5.6 Frontend (TDD-07)** — Next.js dashboard; voice+text; the real AUH map with
  live route; structured-output panel.

## 6. Evaluation & Results (TDD-08) ⭐
- **Methodology** — reproducible in-process harness (deterministic offline agent +
  mock + keyword KB), labeled ar/ary/fr/en scenario set; metrics defined.
  Tooling: `evaluation/run_eval.py` → `evaluation/reports/system_eval.md`.
- **ASR** — the §4 table (headline).
- **System** — comprehension (**intent 100%**), tool correctness (100%), answer-fact
  grounding (100%), **language match 89%**, FAQ retrieval hit-rate, **latency p50/p95**,
  **robustness 4/4** (flight-API down, LLM-failure→offline, unknown flight, code-mixed).
- **Limitations** — Darija FAQ retrieval & language-ID weaker than ar/fr/en (honest
  discussion); AirLabs free-tier transience; CPU TTS quality.

## 7. Deployment & Reproducibility (TDD-09)
- Docker images (CPU torch), `docker-compose` **light** (runs anywhere, no keys) vs
  **full** (real Whisper/RAG/TTS + live providers); CI; config-over-code & secret
  handling; PaaS notes. See `deploy/` + root `README.md`.

## 8. Discussion
- The multilingual challenge as the *core* difficulty (not an afterthought) — where it
  was hardest (Darija ASR vs Darija retrieval).
- Owned-model vs infrastructure boundary and why it satisfies the grading constraint.
- Engineering trade-offs (offline-first, airport-agnostic, typed identity).
  Ethics/privacy (no audio-side PII; keys server-side).

## 9. Conclusion & Future Work
- Summary of contributions and results. Future: larger Darija ASR corpus, stronger
  Arabic embedder, WebSocket streaming, live PaaS, second-airport demo (proves agnosticism).

## References · Appendices
- Appendices: full API contract, config/env reference, scenario dataset, extra eval
  tables, repo map, reproduction commands.

---

### Submission deliverables (from `PROJECT_REQUIREMENTS.md`)
- **PPTX** presentation (Google Drive link) — condense §1, §4, §6.
- **GitHub repo** + `README.md` (done) — code + environment setup.
- **Video** ≤ 7 min (Google Drive link) — project explanation + environment setup +
  demo (§5.6 UI walk-through + a live §6 robustness moment).
