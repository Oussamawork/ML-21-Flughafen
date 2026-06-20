# TDD-06 — Backend REST API & WebSockets

**Component:** `backend/`
**Status:** ⚪ Not started
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
| `POST` | `/chat` | `{text, session_id?, airport_id?, language?}` | `AgentResult` |
| `POST` | `/speak` | `{text, language}` | audio stream (`audio/mpeg`) |
| `POST` | `/converse` | multipart audio + `session_id?` | `{text_in, answer, language, audio_url}` |
| `GET` | `/airports` | — | available `airport_id`s |

- `/converse` is the one-shot voice pipeline: STT → agent → TTS, for the simplest
  demo path.

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
- Models loaded once at startup (lifespan event); heavy (Whisper) optional via
  `LOAD_STT` flag so the API can boot without GPU for agent-only dev.

## 4. Interfaces & data contracts

```jsonc
// POST /chat request
{ "text": "ayna bawwabati rihlati SV-624", "session_id": "abc", "airport_id": "AUH" }

// POST /chat response  (AgentResult, see TDD-02)
{ "answer": "...", "language": "ar", "intent": "find_gate", "tool_trace": [...],
  "session_id": "abc", "latency_ms": { "agent": 820 } }

// POST /converse response
{ "text_in": "...", "answer": "...", "language": "ar", "audio_url": "/audio/xyz.mp3",
  "latency_ms": { "stt": 540, "agent": 820, "tts": 410 } }
```

## 5. Dependencies

`fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `websockets`; plus the
components (TDD-01/02/05). Env: model paths, provider keys, `LOAD_STT`,
`SESSION_TTL`.

## 6. Open questions / risks

- **Whisper hosting** — GPU vs CPU latency for `/transcribe` in the demo.
- **Streaming audio over WS** vs simple request/response (start simple, iterate).
- **Audio delivery** — return bytes vs. temp `audio_url`; pick `audio_url` for
  the web player + a cleanup job.
- **Concurrency** — model thread-safety; use a single worker or a model lock.

## 7. Task checklist

- [ ] FastAPI app + lifespan model loading + `/health`
- [ ] `/transcribe`, `/chat`, `/speak`
- [ ] `/converse` one-shot pipeline + per-stage timing
- [ ] `WS /ws/{session_id}`
- [ ] Session store + TTL
- [ ] Pydantic schemas + OpenAPI docs + CORS
