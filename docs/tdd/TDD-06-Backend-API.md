# TDD-06 — Backend REST API & WebSockets

**Component:** `backend/`
**Status:** 🟡 In progress (skeleton built with offline stubs; tests passing)
**Depends on:** TDD-01, TDD-02, TDD-05 · **Consumed by:** TDD-07 (frontend)

---

## 1. Purpose

Expose the whole system as a service: orchestrate STT → agent → TTS, hold session
state, and provide both a REST API and a real-time WebSocket channel.

## 2. Requirements satisfied

- *Expose the system through a REST API* (and the supervisor's "must be an API").
- *FastAPI with WebSockets for real-time interaction.*

## 3. Design

### 3.1 Stack
- **FastAPI** (async) + **Uvicorn**. Pydantic models for all request/response
  bodies. CORS enabled for the web demo.

### 3.2 Endpoints (REST)

| Method | Path | Body | Returns |
|---|---|---|---|
| `GET` | `/health` | — | `{status, version}` |
| `POST` | `/transcribe` | multipart audio | `{text, language}` |
| `POST` | `/chat` | `{text, session_id?, airport_id?, language?, flight_number?, position?}` | `AgentResult` |
| `POST` | `/speak` | `{text, language}` | audio stream (`audio/mpeg`) |
| `POST` | `/converse` | multipart audio + `session_id?` + `airport_id?` + `flight_number?` + `position?` | `{text_in, answer, language, audio_url, flight?, route?}` |
| `POST` | `/flight` | `{flight_number, airport_id?, position?}` | normalized flight card (+ `route` if `position`) |
| `GET` | `/map` | `?airport_id=AUH` | `{nodes, positions, edges}` (render empty map + position options) |
| `GET` | `/airports` | — | available `airport_id`s (default `AUH`) |

- `/converse` is the one-shot voice pipeline: STT → agent → TTS, for the simplest
  demo path.
- `/flight` powers the ticket-first dashboard: the user types a flight number and
  the UI loads the **flight card + map route** before any chat (mirrors the typed-
  identity rule, TDD-00). `/map` feeds the empty airport map + "I am here" options.
- `flight_number`/`position` are **structured fields** (never parsed from audio);
  `airport_id` defaults to `AUH`.

### 3.3 WebSocket
- `WS /ws/{session_id}` — turn-based real-time:
  - client → `{type:"audio"|"text", data, language?}`
  - server → `{type:"partial_transcript"|"answer"|"audio"|"error", ...}`
- Keeps the session warm; streams answer + audio as ready.

### 3.4 Session management
- In-memory store (dict) keyed by `session_id`, holding `messages`, `language`,
  `airport_id`. Pluggable to Redis later. TTL eviction.
- Session is created on first request if `session_id` omitted (server returns it).

### 3.5 Orchestration
- `/converse` and `/ws` call: `WhisperTranscriber` (TDD-01) → `run_agent`
  (TDD-02) → `TTSProvider` (TDD-05). Each stage timed → logged for TDD-08.
- The agent's flight tool calls **AirLabs** server-side (TDD-03) using
  `AIRLABS_API_KEY`; the backend **strips the AirLabs `request`/meta block** (it
  echoes the key) before anything is returned to the client. The frontend never
  talks to AirLabs directly.
- Models loaded once at startup (lifespan event); heavy (Whisper) optional via
  `LOAD_STT` flag so the API can boot without GPU for agent-only dev.

## 4. Interfaces & data contracts

```jsonc
// POST /chat request — flight_number & position are typed, never from STT
{ "text": "فين البوابة ديالي", "session_id": "abc", "airport_id": "AUH",
  "flight_number": "SV624", "position": "entrance" }

// POST /chat response  (AgentResult, see TDD-02)
{ "answer": "...", "language": "ary", "intent": "find_gate", "tool_trace": [...],
  "flight": { "gate": "B12", "terminal": "A", "status": "scheduled" },
  "route": { "route": ["entrance","...","gate-b12"],
             "route_summary": { "distance_m": 525, "walking_time_min": 7 } },
  "session_id": "abc", "latency_ms": { "agent": 820 } }

// POST /flight request / response (ticket-first dashboard load)
// req:  { "flight_number": "SV624", "airport_id": "AUH", "position": "entrance" }
// resp: { "flight": {...AirLabs-normalized, source:"airlabs"}, "route": {...} }

// POST /converse response
{ "text_in": "...", "answer": "...", "language": "ar", "audio_url": "/audio/xyz.mp3",
  "flight": {...}, "route": {...},
  "latency_ms": { "stt": 540, "agent": 820, "tts": 410 } }
```

## 5. Dependencies

`fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `websockets`; plus the
components (TDD-01/02/05) and the flight tool (TDD-03). Env: model paths,
`LOAD_STT`, `SESSION_TTL`, `AIRLABS_API_KEY` (server-side), `FLIGHT_CACHE_TTL`,
LLM/TTS provider keys.

## 6. Open questions / risks

- **Whisper hosting** — GPU vs CPU latency for `/transcribe` in the demo.
- **Streaming audio over WS** vs simple request/response (start simple, iterate).
- **Audio delivery** — return bytes vs. temp `audio_url`; pick `audio_url` for
  the web player + a cleanup job.
- **Concurrency** — model thread-safety; use a single worker or a model lock.

## 7. Task checklist

- [x] FastAPI app + lifespan service loading + `/health`
- [x] `/transcribe`, `/chat`, `/speak`
- [x] `/converse` one-shot pipeline + per-stage timing
- [x] `WS /ws/{session_id}`
- [x] Session store + TTL
- [x] Pydantic schemas + OpenAPI docs + CORS
- [x] Offline stubs (STT/agent/TTS) + end-to-end tests (`pytest`, 14 passing)
- [x] Swap stub STT → fine-tuned Whisper (`LOAD_STT=true` → `Amassu/whisper-small-darija`)
- [ ] Add `flight_number`/`position` to `/chat` & `/converse`; default `airport_id=AUH`
- [ ] `POST /flight` (ticket-first card + route) and `GET /map` endpoints
- [ ] AirLabs flight tool wired server-side; strip `request`/meta (key echo) from responses
- [ ] Swap stub agent → LangGraph (TDD-02) and stub TTS → provider (TDD-05)

> **Implementation note:** STT/agent/TTS are interfaces in `app/services/` with
> offline stubs, so the API runs with no GPU/keys. The agent stub does simple
> intent + a mock flight tool; replace behind the same `run()` signature.
