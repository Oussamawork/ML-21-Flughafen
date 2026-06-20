# TDD-00 — System Overview

**Project:** Multilingual Smart Airport Wayfinding Assistant
**Case study:** Sheikh Zayed International Airport (AUH), Abu Dhabi
**Status:** 🟡 In progress (design)
**Owner:** Oussama Louhaibi · **Supervisor:** Abdelhak Mahmoudi

> This is the master Technical Design Document. It defines the end-to-end
> architecture and links the component TDDs (01–09). Read this first.

---

## 1. Purpose

Provide a single source of truth for the system architecture: what the components
are, how a request flows through them, the contracts between them, and the
cross-cutting design rules every component must follow (multilingual support,
airport-agnostic design, configuration, observability).

## 2. Requirements satisfied

From `../../PROJECT_REQUIREMENTS.md` and `../Proposition_Projet_Wayfinding.md`:

- **Own/fine-tune a model, not just call an API** → fine-tuned Whisper (TDD-01).
- **Multilingual (Arabic/Darija/French/English)** → STT, agent, TTS, KB.
- **Expose everything as an API** → FastAPI REST + WebSockets (TDD-06).
- **Agentic architecture with tool-calling** → TDD-02 / TDD-03.
- **Airport-agnostic, demoed on AUH** → KB design (TDD-04).
- **Evaluation** → comprehension accuracy, latency, answer quality, WER (TDD-08).

## 3. High-level architecture

```
                         ┌─────────────────────────────────────────────┐
   Passenger             │              Web Demo (Next.js)              │  TDD-07
  (voice / text) ───────▶│   mic capture · chat UI · audio playback     │
                         └───────────────┬───────────────▲─────────────┘
                                         │ REST / WebSocket│
                         ┌───────────────▼───────────────┴─────────────┐
                         │            FastAPI Backend                   │  TDD-06
                         │   /chat · /transcribe · /speak · /ws         │
                         └───┬──────────┬──────────────┬───────────┬────┘
                             │          │              │           │
                   ┌─────────▼──┐  ┌────▼─────┐  ┌─────▼──────┐ ┌──▼─────────┐
                   │  STT       │  │  LLM     │  │   TTS      │ │ Knowledge  │
                   │ Whisper FT │  │ Agent    │  │ synthesis  │ │ Base (RAG) │
                   │  TDD-01    │  │ TDD-02   │  │  TDD-05    │ │  TDD-04    │
                   └────────────┘  └────┬─────┘  └────────────┘ └─────▲──────┘
                                        │ tool calls                  │ retrieve
                                   ┌────▼───────────────────────────┐ │
                                   │           Agent Tools          │─┘
                                   │ flight_status · gate_finder ·  │  TDD-03
                                   │ services_search · faq (RAG)    │
                                   └────┬───────────────────────────┘
                                        │ external
                                   ┌────▼─────────┐
                                   │ Flight Data  │ (AviationStack / AeroDataBox)
                                   │     API      │
                                   └──────────────┘
```

## 4. End-to-end request flow (voice example)

1. **Capture** — user speaks; the web UI streams/uploads audio (TDD-07).
2. **STT** — `POST /transcribe` → fine-tuned Whisper returns text + detected
   language (TDD-01).
3. **Agent** — `POST /chat` with the text. The LLM agent detects intent and
   decides which tool(s) to call (TDD-02).
4. **Tools / RAG** — agent calls e.g. `flight_status("SV-624")` and/or retrieves
   from the airport KB (TDD-03, TDD-04).
5. **Compose** — agent writes a contextual answer in the passenger's language.
6. **TTS** — `POST /speak` converts the answer to audio in that language (TDD-05).
7. **Respond** — text + audio returned to the UI; audio auto-plays.

The synchronous path is also available over a single **WebSocket** session for
low-latency, turn-based interaction (TDD-06).

## 5. Component contracts (summary)

| Component | Input | Output | TDD |
|---|---|---|---|
| STT | audio bytes (wav/mp3) | `{text, language}` | 01 |
| Agent | `{text, language?, session_id}` | `{answer, language, tool_trace[]}` | 02 |
| Tools | typed args (per tool schema) | typed JSON result | 03 |
| RAG | `{query, airport_id, k}` | `{chunks[], sources[]}` | 04 |
| TTS | `{text, language}` | audio bytes (mp3) | 05 |
| Backend | HTTP/WS | the above, orchestrated | 06 |

Full schemas live in each component TDD.

## 6. Cross-cutting design rules

- **Language is a first-class field.** Every boundary (STT→agent→TTS) carries an
  explicit BCP-47-ish language code (`ar`, `ary` Darija, `fr`, `en`). The agent
  must answer in the same language it received.
- **Airport-agnostic.** No airport facts are hard-coded. All airport-specific
  data lives in the KB keyed by `airport_id` (default `AUH`). Adding an airport =
  adding a data pack + config, no code changes (TDD-04).
- **Config over code.** Models, API keys, airport id, and thresholds come from
  environment variables / config files, never literals.
- **Stateless services, session at the edge.** Components are stateless; session
  context (history, language, airport) is held by the backend keyed by
  `session_id`.
- **Graceful degradation.** If the flight API is down, the agent says so and
  falls back to KB/FAQ rather than failing the whole turn.
- **Observability.** Each turn logs: latency per stage, tools called, detected
  language, token usage — feeds TDD-08 evaluation.

## 7. Repository layout (target)

```
ML-21-Flughafen/
├── PROJECT_REQUIREMENTS.md          # supervisor's requirements
├── docs/
│   ├── Proposition_Projet_Wayfinding.md
│   ├── PLAN_ASR_Whisper.md
│   ├── PROGRESS.md                  # cross-session progress log
│   └── tdd/                         # this folder (TDD-00 … TDD-09)
├── asr_finetuning/                  # TDD-01 (built)
├── agent/                           # TDD-02 + TDD-03
├── knowledge_base/                  # TDD-04
├── speech/                          # TDD-05 (TTS) + STT serving glue
├── backend/                         # TDD-06 (FastAPI)
├── frontend/                        # TDD-07 (Next.js)
├── evaluation/                      # TDD-08
└── deploy/                          # TDD-09 (Docker, compose, infra)
```

## 8. Technology stack & rationale

| Layer | Choice | Why |
|---|---|---|
| STT | **Whisper-small, fine-tuned** | The owned ML contribution; Darija support. |
| Agent | LangGraph / LangChain | Explicit tool-calling graph, inspectable state. |
| LLM | GPT-4o-mini or Llama 3.1 (Groq) | Cheap, fast, tool-calling capable. |
| RAG store | ChromaDB | Lightweight, local, no infra. |
| TTS | ElevenLabs / Azure Speech | High-quality multilingual voices. |
| Flight data | AviationStack / AeroDataBox | Live flight status + gates. |
| Backend | FastAPI + WebSockets | Async, typed, real-time. |
| Frontend | Next.js / React | Voice UI + chat demo. |
| Deploy | Docker → Railway/Render | Reproducible, simple PaaS. |

> Note on "fine-tune, not just an API": the LLM, TTS, and flight data remain
> external APIs by design — they are infrastructure. The graded ML contribution
> is the **fine-tuned Whisper** (and optionally a fine-tuned intent classifier,
> tracked as a stretch goal in TDD-02).

## 9. Milestones

1. **M1 — Speech in:** fine-tuned Whisper + `/transcribe`. (TDD-01, TDD-06)
2. **M2 — Brain:** agent + tools + flight API. (TDD-02, TDD-03)
3. **M3 — Knowledge:** AUH KB + RAG. (TDD-04)
4. **M4 — Speech out + UI:** TTS + web demo end-to-end. (TDD-05, TDD-07)
5. **M5 — Eval + deploy:** metrics, Docker, video demo. (TDD-08, TDD-09)

## 10. Glossary

- **STT / ASR** — Speech-to-Text / Automatic Speech Recognition.
- **TTS** — Text-to-Speech.
- **Agent** — LLM that chooses and invokes tools to fulfil a request.
- **Tool** — a typed function the agent can call (e.g. flight_status).
- **RAG** — Retrieval-Augmented Generation: retrieve KB chunks, ground the answer.
- **WER / CER** — Word/Character Error Rate (ASR metrics).
- **Darija** — Moroccan Arabic dialect (`ary`).
- **Airport-agnostic** — works for any airport by swapping data, not code.

## 11. Open questions / risks

- Final LLM choice (hosted GPT-4o-mini vs. self-hosted Llama) — affects cost,
  privacy, and the "owned model" story. Decided in TDD-02.
- Darija dataset availability for Whisper — see TDD-01.
- Flight API free-tier limits (rate, gate coverage at AUH) — see TDD-03.
- Real-time audio over WebSocket vs. simple request/response — see TDD-06.
