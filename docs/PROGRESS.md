# Project Progress Log

Cross-session source of truth for **what's done, what's next, and key decisions**.
Update this at the end of every working session so any future session (human or
AI) can resume without re-reading everything.

**Project:** Multilingual Smart Airport Wayfinding Assistant (case study: AUH)
**Branch:** `feat/tdd-07-dashboard`

---

## 1. Component status

Legend: ⚪ Not started · 🟡 In progress · 🟢 Done · 🔵 Blocked

| Component | TDD | Status | Notes |
|---|---|---|---|
| System overview / architecture | TDD-00 | 🟢 | Design written |
| STT — fine-tuned Whisper | TDD-01 | 🟢 | **Fine-tuned: WER 108→28.8%, CER 64→9.6%** (DODa); pushed to `Amassu/whisper-small-darija`; wired into TDD-06 backend (`LOAD_STT=true`) |
| LLM agent (LangGraph) | TDD-02 | ⚪ | Designed |
| Agent tools + flight API | TDD-03 | 🟡 | AirLabs flight provider + `/flight` built (mock default; live-verified); KB tools (services/directions/faq) pending |
| Knowledge base + RAG | TDD-04 | ⚪ | Designed |
| TTS | TDD-05 | ⚪ | Designed |
| Backend API (FastAPI) | TDD-06 | 🟡 | Fine-tuned Whisper STT on by default (`LOAD_STT=true`); `/health` exposes `stt_loaded` + `whisper_model`; agent/TTS still stubs; 14 tests passing |
| Frontend (Next.js) | TDD-07 | 🟡 | Dashboard: chat + **flight-info card** (typed flight no → `/flight`, live-verified vs mock); text+voice, RTL, airport selector, tool trace; build green. Map panel placeholder (needs `/map`) |
| Evaluation | TDD-08 | ⚪ | Designed |
| Deployment (Docker) | TDD-09 | ⚪ | Designed |

**Milestones:** M1 Speech-in · M2 Brain · M3 Knowledge · M4 Speech-out+UI ·
M5 Eval+Deploy. → Currently inside **M1**.

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
- [ ] LLM choice for the agent: GPT-4o-mini (default) vs Llama 3.1 via Groq.
- [x] ~~Flight API provider that returns **gate/terminal** for AUH on free tier~~ →
      **AirLabs** confirmed: `dep_terminal` ~98%, `dep_gate` ~89% on live AUH
      departures, free tier 1,000 req/month. **No check-in field** → source it from
      the KB. `arr_baggage` arrival-only. Caching mandatory (1,000/mo cap).
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

### Session 2026-06-21 (cont.) — backend STT default
- **STT is now the default path:** `LOAD_STT=true` in config + `.env.example`;
  `backend/.env` auto-loaded via `python-dotenv`. README documents one-shot install
  (`requirements.txt` + `asr_finetuning/requirements.txt`) and a `/health` check.
- **`GET /health`** returns `whisper_model` when the real STT is active — confirms
  `Amassu/whisper-small-darija` (or a local ckpt) is loaded.
- Tests keep stub STT via `tests/conftest.py` (`LOAD_STT=false`).

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
