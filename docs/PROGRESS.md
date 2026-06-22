# Project Progress Log

Cross-session source of truth for **what's done, what's next, and key decisions**.
Update this at the end of every working session so any future session (human or
AI) can resume without re-reading everything.

**Project:** Multilingual Smart Airport Wayfinding Assistant (case study: AUH)
**Branch:** `feat/tdd-08-evaluation`

---

## 1. Component status

Legend: ⚪ Not started · 🟡 In progress · 🟢 Done · 🔵 Blocked

| Component | TDD | Status | Notes |
|---|---|---|---|
| System overview / architecture | TDD-00 | 🟢 | Design written |
| STT — fine-tuned Whisper | TDD-01 | 🟢 | **Fine-tuned: WER 108→28.8%, CER 64→9.6%** (DODa); pushed to `Amassu/whisper-small-darija`; wired into TDD-06 backend (`LOAD_STT=true`) |
| LLM agent (LangGraph) | TDD-02 | 🟢 | **LangGraph agent built + default-on** (`AGENT_BACKEND=langgraph`); LLM behind a provider interface, **offline default (no key)**, Groq/OpenAI when keyed; calls flight + KB tools; live-verified |
| Agent tools + flight API | TDD-03 | 🟢 | AirLabs flight provider + `/flight` (mock default; live-verified); **full tool catalogue wired**: `flight_status`/`find_gate` + KB `directions`/`find_service`/`faq` |
| Knowledge base + RAG | TDD-04 | 🟢 | **Built** in `backend/app/kb/`: per-`airport_id` YAML pack + map-graph `directions` + service index + **ChromaDB/multilingual-e5 FAQ RAG** (retriever interface: chroma default, keyword for tests); `/map` endpoint; live-verified (semantic EN/FR/AR; Darija weaker — see open Qs) |
| TTS | TDD-05 | 🟢 | **Built** — real **local MMS-TTS** (`facebook/mms-tts-{ara,fra,eng}`, on-CPU, no key, `TTS_PROVIDER=local` default) behind the existing `TTS` interface; `/speak`+`/converse` now speak; ar/fr/en (Darija→Arabic); live-verified. Hosted **ElevenLabs** (`TTS_PROVIDER=elevenlabs`) merged — natural voice that reads gate codes/numbers, degrades to MMS on error. Tests keep stub TTS |
| Backend API (FastAPI) | TDD-06 | 🟢 | All stages real: STT (fine-tuned Whisper, `LOAD_STT=true`), agent (LangGraph), KB+RAG, TTS (local MMS-TTS); `/health` reports active backends; `/transcribe /chat /speak /converse /flight /map /airports` + WS; 61 tests passing |
| Frontend (Next.js) | TDD-07 | 🟡 | **SkyGuide-identical redesign**: landing page + 4-card dashboard (Flight `/flight` + KB check-in, Agent chat+mic on the real agent, **live Map route from `/map`**, JSON proof); live-verified; build green. Remaining: optional WebSocket streaming |
| Evaluation | TDD-08 | 🟢 | **Built** — `evaluation/` harness scores intent/tool/facts/language/FAQ-hit/latency/robustness over a labeled ar/ary/fr/en set vs the deterministic offline agent (reproducible). Latest: intent 100%, facts 100%, tools 100%, lang 89%, robustness 4/4; report `evaluation/reports/system_eval.md`; pytest guard `tests/test_eval.py` |
| Deployment (Docker) | TDD-09 | ⚪ | Designed |

**Milestones:** M1 Speech-in · M2 Brain · M3 Knowledge · M4 Speech-out+UI ·
M5 Eval+Deploy. → **M4 done** (real local TTS; the whole STT→agent→KB→TTS pipeline
now runs for real, offline/key-free). Next: **M5** — evaluation (TDD-08) + Docker
deployment (TDD-09).

## 2. Key decisions (chronological)

- **2026-06-20** Domain confirmed: airport wayfinding (not pharmacy); cleared with
  supervisor. Repo name "Flughafen" = airport.
- **2026-06-20** Owned ML contribution = **fine-tuned Whisper (Darija/Arabic)** to
  satisfy "fine-tune, don't just call an API". LLM/TTS/flight data stay as
  external APIs (infrastructure).
- **2026-06-20** Whisper base = **whisper-small**; dataset = public HF
  (configurable), default Common Voice Arabic; metric WER+CER.
- **2026-06-20** Documentation approach: one TDD per component (TDD-00…09) +
  this progress log. All written in full detail upfront.
- **2026-06-20** PR #1 (initial docs + ASR scaffold) merged into `main`.
- **2026-06-20** Workflow: **one branch + one PR per TDD/component** going
  forward. Each implementation gets a dedicated branch off `main`
  (e.g. `feat/tdd-06-backend`) with its own scoped PR. Merged TDD docs stay as-is.
- **2026-06-21** ✅ **TDD-01 fine-tune complete.** `whisper-small` on DODa:
  WER 108.18%→28.79%, CER 63.76%→9.63% (1,259-sample sentence-grouped held-out).
  The owned ML contribution is now a measured, strong result.
- **2026-06-21** ✅ **STT wired into the backend** (`LOAD_STT=true` → fine-tuned
  Whisper; PR #10). Voice round-trip verified end-to-end through the frontend.
- **2026-06-21** **Product decisions after reviewing the teammate's "SkyGuide"
  build** (the parallel prototype in `~/Documents/Private/projet_ml_ch`):
  - **R1 — Flight/ticket number is a typed, structured input, not parsed from
    audio.** STT+LLM can't reliably extract a code like `SV624` from Darija/noisy
    speech. Voice is for natural questions; the flight number is entered in a field.
  - **R2 — `airport_id` stays first-class but defaults to `AUH`** unless specified
    (keeps the airport-agnostic design; matches SkyGuide's AUH default).
  - **R3 — "I am here" current-position selector** so routing/answers are relative
    to the user's location (position = a node in the KB layout graph).
  - **R4 — Flight-data provider = AirLabs** (v9). External infrastructure; the
    owned-model requirement stays satisfied by Whisper.
  - **Frontend evolves from chat-only to a dashboard** (chat + Flight-Info card +
    Airport-Map panel + Structured-Output panel), porting and surpassing SkyGuide.
    The airport map is **our** data (KB, keyed by `airport_id`), seeded from
    SkyGuide's `airport_map.json` + edge distances — *not* hard-coded AUH.
- **2026-06-21** ✅ **AirLabs verified on a live free-tier key.** `/flight?flight_iata=`
  is the primary lookup; `dep_terminal` 98% / `dep_gate` 89% / `status` 100% coverage
  on real AUH departures; `arr_baggage` is arrival-only (~35%). Free tier =
  **1,000 req/month**, 250/min, 2,500/hr. **No check-in field** (→ KB). `/flight`
  can't filter by airport (scope in code). Response **echoes the api_key** → backend
  must strip meta before returning to the FE. Key stays server-side, never committed.
- **2026-06-21** **No new TDDs needed** for the dashboard/map: it maps onto TDD-04
  (map graph + positions + check-in data), TDD-03 (`directions` route tool +
  AirLabs flight tool), TDD-06 (request contract + `/flight` & `/map` endpoints),
  and TDD-07 (dashboard UI). TDD-00/02/03/04/06/07 updated accordingly.

## 3. Open questions / to resolve

- [x] ~~Verify a real **Darija ASR dataset**~~ → chose `atlasia/DODa-audio-dataset`
      (DODa, ~9h46m), wired as `config/doda_darija.yaml`. Schema confirmed on the
      Hub: `train` split only; Arabic-script column `darija_Arab_new`. Eval set is
      carved from train with a sentence-grouped split (no leakage). Dataset is gated.
- [x] ~~LLM choice for the agent: GPT-4o-mini vs Llama 3.1 via Groq~~ → **deferred
      via a provider interface** (`LLM_PROVIDER`): default **`offline`** (deterministic,
      no key) so the agent runs key-free; `openai` (GPT-4o-mini) / `groq` (Llama 3.1)
      are lazy-imported, model picked when a key is wired. Whisper stays the owned model.
- [x] ~~Flight API provider that returns **gate/terminal** for AUH on free tier~~ →
      **AirLabs** confirmed: `dep_terminal` ~98%, `dep_gate` ~89% on live AUH
      departures, free tier 1,000 req/month. **No check-in field** → source it from
      the KB. `arr_baggage` arrival-only. Caching mandatory (1,000/mo cap).
- [x] ~~KB retrieval/embeddings~~ → **ChromaDB + `intfloat/multilingual-e5-base`**
      (local CPU, no key), behind a `KB_RETRIEVER` interface (`chroma` default,
      `keyword` for tests). Built; semantic EN/FR/AR retrieval verified.
- [ ] **Darija FAQ retrieval is weaker** than ar/fr/en with e5-base (short Darija
      queries mis-rank). Acceptable for the demo (RAG is infra; the owned Darija
      model is Whisper). If needed: try a stronger/Arabic-tuned embedder or expand
      Darija FAQ phrasings.
- [ ] Where to run Whisper in the deployed demo (CPU latency vs hosted STT).
- [ ] AirLabs free tier is only **1,000 req/month** — confirm caching strategy is
      enough for the demo, or budget a paid tier for the live presentation.

## 4. Session log

### Session 2026-06-20
- Read supervisor's project brief → `PROJECT_REQUIREMENTS.md` (committed).
- Analyzed Wayfinding proposal; flagged the "must fine-tune" gap → chose Whisper.
- Built `asr_finetuning/` pipeline (config, data, train, eval, transcribe) +
  README; config loader unit-tested locally (no GPU here).
- Saved proposal (`docs/Proposition_Projet_Wayfinding.md`) + ASR plan
  (`docs/PLAN_ASR_Whisper.md`).
- Wrote full TDD set `docs/tdd/TDD-00…09` + this progress log.
- **Next session:** verify Darija dataset; run baseline + smoke test on a GPU
  (Colab/Kaggle); then start TDD-02 agent scaffold.

### Session 2026-06-20 (cont.) — TDD-01 Darija dataset
- Researched Darija ASR datasets on the HF Hub (PR #1, #2 already merged).
- Chose **DODa** (`atlasia/DODa-audio-dataset`) as primary Darija set; added
  `config/doda_darija.yaml`. Documented alternatives (DVoice, Darija-Wiki, FLEURS).
- Hardened `data.load_splits`: auto-carve validation split when none exists;
  fail-fast with available columns on a mismatch. Added `dataset.test_size`.
- Updated ASR README, TDD-01, PROGRESS. Branch `feat/tdd-01-darija-dataset`.
- **Next:** verify DODa column names/splits in the HF viewer, then baseline +
  smoke test on a GPU.

### Session 2026-06-20 (cont.) — TDD-01 training notebook
- PR #4 merged. Added click-to-run Colab/Kaggle notebook
  `asr_finetuning/notebooks/finetune_whisper_colab.ipynb` (GPU check → clone →
  install → HF login → smoke test → baseline eval → fine-tune → eval → push to
  Hub → listen test). Works in browser Colab and the VS Code Colab extension.
- Linked it from the ASR README; ticked the notebook item in TDD-01.
- Branch `feat/tdd-01-colab-notebook`. **Next:** run it on a T4 to get the
  base-vs-fine-tuned WER, then wire `WhisperTranscriber` into TDD-06.

### Session 2026-06-20 (cont.) — TDD-06 backend skeleton
- PR #5 (notebook) merged. Started backend on `feat/tdd-06-backend`.
- Built FastAPI app: `/health`, `/airports`, `/transcribe`, `/chat`, `/speak`,
  `/converse` (STT→agent→TTS + per-stage latency), `/audio/{id}`, `WS /ws/{id}`;
  in-memory session store with TTL; CORS; OpenAPI docs.
- STT/agent/TTS are interfaces with **offline stubs** so it runs with no GPU/keys:
  stub STT returns a Darija sample, stub agent does intent + a mock flight tool
  (SV624→gate B12), stub TTS returns a silent WAV. Real impls swap in per TDD.
- `pytest`: **11 tests passing** (incl. full `/converse` + WebSocket).
- Wired `WhisperSTT` adapter (lazy) for when `LOAD_STT=true` post-training.
- **Next:** real Whisper once the checkpoint exists; then TDD-02 agent / TDD-07
  frontend can consume this API.

### Session 2026-06-21 — TDD-01 loader + smoke-test fixes
- Fixed DODa load crash: filter ~22 null `darija_Arab_new` rows before grouped split.
- Hardened audio loading (`decode=False` + soundfile/librosa) for Mac CPU / no FFmpeg.
- Pointed `scripts/smoke_test.sh` at DODa (Common Voice 17 broken on `datasets>=4`).
- Updated Colab notebook clone cell (git pull + hotfix). Smoke test verified locally.
- Branch `fix/tdd-01-doda-loader-smoke`. **Next:** full fine-tune on Colab T4.

### Session 2026-06-21 (cont.) — merge main into TDD-06 backend
- Merged the TDD-01 loader/smoke fixes (PR #7) into `feat/tdd-06-backend`;
  resolved the PROGRESS session-log conflict (kept both entries). PR #6 merged.

### Session 2026-06-21 (cont.) — TDD-07 frontend
- Built the Next.js (App Router) demo UI in `frontend/`: text + voice chat that
  calls the backend (`/chat` + `/speak`, and `/converse` for voice), auto-plays
  replies, RTL/LTR per message, EN/FR/AR UI labels, airport selector from
  `/airports`, and a per-message tool-trace + latency panel.
- Typed API client (`lib/api.ts`) mirroring the TDD-06 contracts; `MediaRecorder`
  hook for the mic. Bumped Next to 14.2.35 (security patch).
- Verified locally: `tsc --noEmit` clean + `next build` green (4 static pages).
- Branch `feat/tdd-07-frontend`. PR #8. **Next:** end-to-end demo now backend is
  merged; wire real STT/agent/TTS as they land; optional WebSocket streaming.

### Session 2026-06-21 (cont.) — TDD-01 fine-tune results
- Fine-tune finished on a Colab T4 (3000 steps). Recorded base-vs-fine-tuned eval
  on the DODa held-out set (1,259 samples): **WER 108.18%→28.79%, CER 63.76%→9.63%**
  (73%/85% relative). Base model emitted wrong scripts (Chinese/Hindi) on Darija;
  fine-tuned transcribes correctly.
- Saved `docs/RESULTS_TDD-01.md` (presentation-ready) + `asr_finetuning/MODEL_CARD.md`
  (HF card). Updated TDD-08, TDD-01 checklist. Branch `feat/tdd-01-eval-results`.
- **Pending:** user to push model to `Amassu/whisper-small-darija`; then wire into
  backend via `LOAD_STT=true`. Optional: training curve from `trainer_state.json`.

### Session 2026-06-21 (cont.) — TDD-06 STT integration
- Wired the fine-tuned Whisper into the backend: `WHISPER_MODEL` now defaults to
  `Amassu/whisper-small-darija`, so `LOAD_STT=true` loads the owned model with no
  extra config. `WhisperSTT` refactored into testable seams (`_load_transcriber`,
  `_decode_audio`) so torch/librosa stay off the default import path.
- Added `tests/test_stt_integration.py`: exercises the real `/transcribe` path and
  `build_stt()`/health with the heavy bits monkeypatched (no GPU/model download).
  `pytest`: **14 passing**. Fixed a stale `Oussamawork/...` id in `backend/README.md`.
- Branch `feat/tdd-06-stt-integration`. **Next:** TDD-02 LangGraph agent to replace
  the stub; then the voice round-trip is real STT → real agent.

### Session 2026-06-21 (cont.) — product mapping: flight data + dashboard
- Reviewed the teammate's **SkyGuide** prototype (ran it; its animated airport map,
  flight card, and ticket-first flow are the parts worth adopting).
- Locked decisions **R1–R4** (see §2): typed flight number, `airport_id` default
  AUH, position selector, **AirLabs** as the flight provider; frontend → dashboard.
- Researched + **live-verified AirLabs** on a free key (see §2). `/flight` is the
  primary lookup; gate/terminal well-covered; no check-in field; 1,000 req/mo.
- **Documented everything before building:** updated TDD-00 (flow/stack/risks),
  TDD-02 (agent state + flight_number/position), TDD-03 (AirLabs flight tool +
  route tool), TDD-04 (map graph + positions + check-in, seeded from SkyGuide),
  TDD-06 (request contract + `/flight` & `/map` endpoints), TDD-07 (dashboard).
- **Next:** build order — TDD-03 (AirLabs flight tool, de-risked) then TDD-02
  (agent), then TDD-04 (KB+map) and the TDD-07 dashboard.

### Session 2026-06-21 (cont.) — TDD-03 AirLabs flight tool
- Built the flight provider in `backend/app/services/flight.py`: `FlightProvider`
  interface, `AirLabsProvider` (real `/flight` lookup, normalized, airport-scoped,
  TTL cache, meta stripped) and `MockFlightProvider` (default → offline/tests).
- Added `POST /flight` (TDD-06), `FlightRequest`/`FlightInfo`/`FlightResponse`
  schemas, config (`FLIGHT_API_PROVIDER`/`AIRLABS_API_KEY`/`FLIGHT_CACHE_TTL`).
- **Live-verified** against AirLabs with the real key (EK201 normalized correctly).
  Found + fixed a real bug: AirLabs **403s the default urllib User-Agent** → set one.
- `pytest`: **25 passing** (mock provider, normalization, dep/arr scoping, caching,
  graceful errors, endpoint 200/404/503). Branch `feat/tdd-03-flight-tool`.
- **Next:** TDD-02 agent (expose `flight_status` as a tool) + TDD-04 KB/map (route).

### Session 2026-06-21 (cont.) — TDD-07 dashboard: flight-info card
- Chose to advance the **frontend** next (FE-first): `/flight` is the one piece of
  the new dashboard direction with a live, verified backend, so the flight card is
  a fully-backed vertical slice (vs. another headless component).
- Adapted the chat-only UI into a **two-column dashboard**: chat column + flight
  aside. New `components/FlightPanel.tsx` = typed flight-number input (R1:
  structured, never parsed from audio) → `POST /flight` → flight card (airline,
  route, gate, terminal, status badge, times, baggage, delay). Airport-scoped;
  clears on airport change. 404→"not found", 503→"unavailable".
- Mirrored `FlightInfo`/`FlightResponse` in `lib/types.ts`; added `getFlight()` +
  `FlightLookupError` in `lib/api.ts`; flight labels in `lib/i18n.ts` (en/fr/ar).
- **Map panel is a placeholder** (needs `/map`, TDD-04); structured-output panel
  pending. `next build` green. **Live-verified** vs the mock backend (EK201 full
  card; unknown number → 404). Branch `feat/tdd-07-dashboard` (off `main`; old
  `feat/tdd-07-frontend` was already merged).
- **Next:** `/map` endpoint + Airport-Map panel (TDD-04/06), then TDD-02 agent so
  chat answers are real.

### Session 2026-06-21 (cont.) — TDD-07 redesign to match SkyGuide
- Per request, **rebuilt the frontend to be visually identical to SkyGuide**
  (teammate's prototype in `~/Documents/Private/projet_ml_ch`). Explored its
  vanilla HTML/CSS/JS, then re-implemented the look in our Next.js + Tailwind.
- **Both screens:** landing page (hero, animated clouds, 6 prep cards) → 4-card
  dashboard (Flight Information, Airport Agent, Airport Map, Structured API Output)
  + ticket strip (flight no · Language · "I am here" · Load). New components:
  `LandingPage`, `TopNav`, `TicketStrip`, `Card`, `FlightCard`, `AgentCard`,
  `MapCard`, `ApiOutputCard`. Deleted the earlier `FlightPanel`/`Header`/`ChatPanel`/
  `MessageBubble`/`Composer`. SkyGuide palette/Inter/cloud+map CSS in
  `tailwind.config.ts`/`globals.css`. Hero image copied to `public/assets/`.
- **Confirmed deviations:** kept **mic capture** in the agent card (SkyGuide is
  text-only) to preserve the fine-tuned Whisper demo; **no airport selector**
  (airport_id defaults to AUH); map renders from an **AUH seed** (`lib/map-seed.ts`,
  from SkyGuide's `airport_map.json`) until `/map` (TDD-04).
- **Flight card mapping:** dark hero (`dep → arr`) + label/value rows; Check-in = `—`
  (KB later), Boarding ← estimated/scheduled, status as plain text.
- **Verified in a headless browser** against the mock backend: landing → dashboard,
  SV624 auto-loads (AUH→RUH, gate B12, terminal A), agent `/chat`→`/speak` fired
  (200s), map shows the green "You" node, JSON proof renders. `next build` green.
- **Next:** `/map` endpoint + live map route (TDD-04/06), then TDD-02 agent.

### Session 2026-06-21 (cont.) — backend STT default
- **STT is now the default path:** `LOAD_STT=true` in config + `.env.example`;
  `backend/.env` auto-loaded via `python-dotenv`. README documents one-shot install
  (`requirements.txt` + `asr_finetuning/requirements.txt`) and a `/health` check.
- **`GET /health`** returns `whisper_model` when the real STT is active — confirms
  `Amassu/whisper-small-darija` (or a local ckpt) is loaded.
- Tests keep stub STT via `tests/conftest.py` (`LOAD_STT=false`).

### Session 2026-06-21 (cont.) — TDD-02 LangGraph agent (M1 → M2)
- Chose to build the **agent** next so the dashboard chat stops being a stub. Built
  the real **LangGraph agent** in `backend/app/agent/` (graph: `detect_lang →
  agent_llm → tools* → compose`, `MAX_TOOL_HOPS=4`), replacing `StubAgent` behind
  the existing `Agent` Protocol (`build_agent()` dispatches on `AGENT_BACKEND`).
- **LLM behind a provider interface** (`LLMProvider.complete`), per the user's
  "decide the model later" call: default **`OfflineProvider`** is deterministic and
  **needs no key** (detects flight code → calls the flight tool → templated
  multilingual answer); `OpenAIProvider`/`GroqProvider` are lazy-imported for when a
  key is wired (`LLM_PROVIDER` switch). Config: `LLM_PROVIDER`/`LLM_MODEL`/`MAX_TOOL_HOPS`.
- **Flight tools** (`flight_status`/`find_gate`, TDD-03) wrap the real `FlightProvider`
  (agent + `/flight` now share one provider via `state.py` injection); `FlightUnavailable`
  degrades gracefully (never crashes the turn).
- **Default flipped to `langgraph`** (offline) in config + `.env.example`. Verified:
  existing 25 API tests pass **unchanged**, + 11 new `tests/test_agent.py` (36 total);
  live `/chat "where is my gate for SV624?"` → grounded answer + `tool_trace`,
  `/health` shows `agent_backend=langgraph`. `langgraph` 1.2.6 installs on Python 3.14.
- **Pre-wired** optional `flight_number`/`position` on `Agent.run`/`AgentState` so
  threading the dashboard's typed flight number through `/chat` later (TDD-06/07) is
  pure plumbing. Branch `feat/tdd-02-agent` (off `main`).
- **Next:** RAG/KB tools + `/map` (TDD-04); wire a real LLM key to pick the model.

### Session 2026-06-21 (cont.) — verified agent on Groq + wired typed flight number
- **Tested the agent with a real LLM (free):** GPT isn't free, so used **Groq** (Llama
  3.3 70B) via the provider interface (`LLM_PROVIDER=groq`, free key in gitignored
  `.env`). Found + fixed a real bug in the hosted path: it **looped tool calls then
  hallucinated** — corrected the tool-call protocol (assistant `tool_calls` + linked
  `tool_call_id` messages), set `temperature=0`, hardened the prompt. Faithful EN/FR
  answers verified live in the dashboard (commit `415e10f`).
- **Whisper decode fix** (`transcribe.py`): `clean_up_tokenization_spaces=False` to
  preserve Arabic/French spacing + silence the BPE warning (commit `35d0907`).
- **Wired the ticket-strip flight number into `/chat` & `/converse`:** `ChatRequest`
  + `converse` form fields gain `flight_number`/`position`; persisted on the
  `Session` (so voice turns stay grounded); `_run_agent_turn` passes them to the
  agent. Frontend (`api.ts`, `page.tsx`) sends the ticket-strip number on ask + mic.
  Now "where is my gate?" (no code) → grounded answer. 38 backend tests; FE build green.
- **Browser-verified** end-to-end on Groq: asked without the code → "Your gate is
  B12, in terminal A." `main` now has the SkyGuide frontend, so this branch carries it too.
- **Next:** TDD-04 (KB + RAG tools + `/map`), then pick the production LLM/model.

### Session 2026-06-21 (cont.) — TDD-04 Knowledge Base + RAG + `/map` (M2 → M3)
- Built the **knowledge base** in `backend/app/kb/` (per-`airport_id` YAML pack:
  airport/layout/services/checkin/faq, AUH seeded from SkyGuide's `airport_map.json`
  + edge table + services + FAQ extended to ar/ary/fr/en). KB lives inside the
  backend package (like the agent), built once in the service container + injected
  into the agent and routes.
- **Map graph `directions`** (BFS + distances ported from SkyGuide) → route + steps +
  positions + summary; **`find_service`** (structured filter); **`faq` RAG** behind a
  `KB_RETRIEVER` interface — **`chroma` default** (ChromaDB + multilingual-e5, local
  CPU, no key) and **`keyword`** (dep-free; tests use it so pytest downloads no model,
  mirrors `LLM_PROVIDER=offline`/`LOAD_STT=false`). `ingest.py` builds the store.
- Wired the three tools into the agent (registry + offline-provider intent routing:
  flight/directions/service/faq/smalltalk; directions chains `flight_status→directions`)
  and added **`POST /map`** + KB `route`/`checkin` on `/flight`; `/airports` now lists
  installed packs. **Frontend**: `MapCard` fetches `/map` and draws the live route
  polyline + distance/walk banner; Check-in filled from `/flight.checkin`.
- **Step 0 gate passed:** chromadb 1.5.9 + sentence-transformers 5.6.0 install/import
  on Python 3.14, coexist with the STT torch stack. **Tests: 55 passing** (was 38;
  +test_kb/test_map + agent KB tests + second-airport agnostic fixture). FE build green.
- **Live-verified** the real chroma path: semantic FAQ (e.g. "my suitcase did not
  arrive"→baggage, "comment me connecter à internet"→wifi with no shared keywords),
  `/map` route SV624→gate-b12 (525 m/7 min), directions chat chain. Darija short
  queries weaker (logged as an open question). Branch `feat/tdd-04-knowledge-base`.
- **Next:** TDD-05 real TTS (last stub) → then M5 eval + deploy.

### Session 2026-06-21 (cont.) — TDD-05 local TTS (M3 → M4 done)
- Replaced the silent `StubTTS` with **real local MMS-TTS** (`MmsTTS` in
  `services/tts.py`): Meta `facebook/mms-tts-{ara,fra,eng}` via the installed
  `transformers`/`torch` — **no key, offline/CPU** (same philosophy as Whisper).
  One model per language (lazy + cached), float→16-bit PCM WAV, bounded phrase cache.
  Behind the existing `TTS` interface → `/speak`+`/converse`+frontend autoplay unchanged.
- **Default flipped** `TTS_PROVIDER=local`; conftest sets `stub` so tests download
  no model (mirrors `LOAD_STT=false`/`KB_RETRIEVER=keyword`). Language→model map is
  config-driven (`TTS_MODEL_<LANG>`); Darija→Arabic voice.
- **Step 0 gate passed:** mms-tts-ara + -eng load + synthesize on Python 3.14 /
  transformers 5.x; **Arabic needs no `uroman`**. **Live-verified** `/speak` for
  en/fr/ar returns real voiced WAVs (53-75 KB). **Tests: 61 passing** (+5 TTS, MMS
  engine faked). Branch `feat/tdd-05-tts`.
- Decision: local-first TTS (user's call) — hosted ElevenLabs/Azure remain a drop-in
  behind the same interface. Limitation: MMS Arabic mispronounces embedded Latin
  (gate "B12"); Darija uses the Arabic voice (TTS is infra; owned model is Whisper).
- **Next:** M5 — TDD-08 evaluation + TDD-09 deployment (Docker).

### Session 2026-06-22 — TDD-08 evaluation (M5)
- Built `evaluation/`: `scenarios.yaml` (27 labeled ar/ary/fr/en cases), `scorers.py`
  (pure), `run_eval.py` (in-process harness vs the deterministic offline agent +
  mock flight + keyword KB → reproducible, key-free), `reports/system_eval.md`.
- Measures comprehension (intent, per-language), tool correctness, answer facts,
  language match, FAQ retrieval hit-rate, agent latency p50/p95, and robustness
  (flight down / LLM-failure→offline / unknown flight / code-mixed).
- **Results:** intent 100%, facts 100%, tools 100%, FAQ-hit 100% (en/fr keyword),
  language 89% (the 3 Darija cases detect as `ar` — documented), latency p50 0.7ms /
  p95 2.8ms, robustness 4/4. ASR headline (WER 108→28.8%) linked from RESULTS_TDD-01.
- Added `tests/test_eval.py` guard (gates intent/facts/tools/robustness) → 65 tests.
- Also fixed a frontend bug (agent chat auto-scroll yanked the whole page down) on a
  separate branch `fix/agent-page-scroll` (PR off main).
- **Next:** TDD-09 (Docker deployment) — the last component.

### Session 2026-06-22 (cont.) — Claude (Anthropic) provider + fallback chain
- Added `AnthropicProvider` (`LLM_PROVIDER=anthropic`, Claude's content-block tool
  API — its own adapter) + a `FallbackProvider`: a hosted primary now degrades
  **Anthropic → Groq → offline** so an outage/limit never crashes the turn.
- Why: Groq (Llama 3.3) leaked English into Darija and mis-grounded (placeholder
  tool args → wrong concourse). **Live-verified Claude Haiku 4.5**: fully-Darija
  output (even "duty free"→"المتاجر الحرة", "Concourse B"→"الصالة B"), clean
  `flight_status`→`directions(gate="B12")`, correct grounding (535 m, Concourse B).
- `anthropic` SDK lazy-imported (offline default still pulls no SDK — asserted in
  tests); config `ANTHROPIC_API_KEY` + `GROQ_FALLBACK_MODEL`. 66 tests.
- **Next:** open the PR; pick the production model (Haiku vs Sonnet) by cost/quality.

### Session 2026-06-22 (cont.) — ElevenLabs hosted TTS
- Added `ElevenLabsTTS` (`TTS_PROVIDER=elevenlabs`) behind the existing `TTS`
  interface: natural multilingual voice that **reads gate codes/numbers** (local
  MMS drops embedded Latin/digits and sounds robotic). Stdlib HTTP, MP3 out,
  phrase-cached (free-tier quota), and **degrades to local MMS on any API error**.
- Config: `ELEVENLABS_API_KEY`/`ELEVENLABS_VOICE_ID`/`ELEVENLABS_MODEL`
  (`eleven_multilingual_v2`). Local MMS stays the no-key default. 67 tests
  (+ fallback/key unit tests; 68 after merge). **Live-verified** voice
  `PmGnwGtnBs40iau7JfoF` (paid plan): `/speak` returns real MP3 reading "B12"/"535".
- End-to-end verified **Claude + ElevenLabs together**: Claude answers SV624 fully in
  Darija (gate B12, Terminal A, 18:55) → ElevenLabs speaks it. **Merged to `main`**
  (after merging updated main carrying the Anthropic provider). **Next:** TDD-09 deploy
  + `docs/readme` are the last open PRs.

<!-- Template for new sessions:
### Session YYYY-MM-DD
- Did: ...
- Decisions: ...
- Next: ...
-->

## 5. How to resume (quick start for a new session)

1. Read this file + `docs/tdd/TDD-00-System-Overview.md`.
2. Check "Component status" + the current milestone.
3. Open the TDD for the component you're working on; follow its task checklist.
4. Do the work; update the component's status here + add a session-log entry.
5. Commit + push to the branch above.
