# Backend — FastAPI (TDD-06)

The service that exposes the assistant: it orchestrates **STT → agent → TTS**,
holds session state, and serves a REST API + a WebSocket. Design:
`../docs/tdd/TDD-06-Backend-API.md`.

> **Runs today with zero GPU / zero API keys.** The STT, agent, and TTS are
> behind interfaces with **offline stubs** (`app/services/`). Real components drop
> in behind the same interfaces: STT=TDD-01, agent=TDD-02/03, TTS=TDD-05.

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://127.0.0.1:8000/docs
```

Configure via env (see `.env.example`): `AIRPORT_ID`, `LOAD_STT`,
`WHISPER_MODEL`, `AGENT_BACKEND`, `TTS_PROVIDER`, `CORS_ORIGINS`, `SESSION_TTL`.

## Test

```bash
cd backend
pip install -r requirements-dev.txt
pytest                              # end-to-end tests against the stubs
```

## Endpoints

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | — | status + which backends are active |
| GET | `/airports` | — | installed `airport_id`s (KB-driven later) |
| POST | `/transcribe` | multipart `audio` | `{text, language, session_id}` |
| POST | `/chat` | `{text, session_id?, airport_id?, language?}` | `ChatResponse` |
| POST | `/speak` | `{text, language}` | audio stream |
| POST | `/converse` | multipart `audio` | STT→agent→TTS: `{text_in, answer, audio_url, latency_ms, …}` |
| GET | `/audio/{id}` | — | the TTS clip produced by `/converse` |
| WS | `/ws/{session_id}` | `{type:'text'\|'audio', data, language?}` | streamed `transcript` / `answer` |

`ChatResponse` carries `answer`, `language`, `intent`, `tool_trace[]`,
`session_id`, and per-stage `latency_ms` (feeds TDD-08 evaluation).

## Layout

```
backend/
├── app/
│   ├── main.py          # FastAPI app, lifespan (builds services), CORS
│   ├── config.py        # env-driven settings
│   ├── schemas.py       # pydantic request/response contracts
│   ├── sessions.py      # in-memory session store + TTL
│   ├── state.py         # process-wide service container
│   ├── routes.py        # REST + WebSocket, STT→agent→TTS orchestration
│   └── services/        # stt / agent / tts (interfaces + offline stubs), lang, audio_store
└── tests/test_api.py    # TestClient end-to-end tests
```

## Enabling the real fine-tuned Whisper

The Darija fine-tune (TDD-01) is on the HF Hub as
[`Amassu/whisper-small-darija`](https://huggingface.co/Amassu/whisper-small-darija)
and is already the default `WHISPER_MODEL`. To load it, set `LOAD_STT=true` and
install the ASR deps:

```bash
pip install -r ../asr_finetuning/requirements.txt
LOAD_STT=true uvicorn app.main:app          # uses Amassu/whisper-small-darija by default
```

Override `WHISPER_MODEL` to point at a local checkpoint or another HF id.
`app/services/stt.py::WhisperSTT` lazily wraps `asr_finetuning`'s
`WhisperTranscriber`, so torch/transformers/librosa are imported only on this path.
