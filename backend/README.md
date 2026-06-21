# Backend — FastAPI (TDD-06)

The service that exposes the assistant: it orchestrates **STT → agent → TTS**,
holds session state, and serves a REST API + a WebSocket. Design:
`../docs/tdd/TDD-06-Backend-API.md`.

> **STT uses the fine-tuned Whisper by default** (`Amassu/whisper-small-darija`,
> TDD-01). The **agent is the LangGraph agent** (`AGENT_BACKEND=langgraph`) with an
> **offline LLM provider** (`LLM_PROVIDER=offline`, no key) that grounds answers in
> the flight tool; set `LLM_PROVIDER=openai`/`groq` + a key for a hosted model. TTS
> is still an offline stub (TDD-05). Flight data defaults to `mock` (no API key).

## Run

```bash
cd backend
pip install -r requirements.txt -r ../asr_finetuning/requirements.txt
cp .env.example .env          # LOAD_STT=true and WHISPER_MODEL already set
uvicorn app.main:app --reload # http://127.0.0.1:8000/docs
```

`.env` is loaded automatically at startup. Override any setting there or via the
shell (`export WHISPER_MODEL=/path/to/checkpoint`).

### Verify the fine-tuned model is active

After startup (first run downloads the model from Hugging Face — may take a minute):

```bash
curl -s http://127.0.0.1:8000/health | python -m json.tool
```

You should see:

```json
{
  "status": "ok",
  "stt_loaded": true,
  "whisper_model": "Amassu/whisper-small-darija",
  "agent_backend": "langgraph",
  "tts_provider": "stub"
}
```

- `stt_loaded: true` — real Whisper STT, not the stub
- `whisper_model` — which checkpoint/HF id is loaded (your fine-tune by default)

Or open http://127.0.0.1:8000/docs → **GET /health** → **Try it out**.

### Stub mode (no GPU / faster boot)

For agent-only development or CI, disable the model:

```bash
LOAD_STT=false uvicorn app.main:app --reload
```

`/health` will then report `"stt_loaded": false` and omit `whisper_model`.

## Configuration

See `.env.example`: `AIRPORT_ID`, `LOAD_STT`, `WHISPER_MODEL`, `AGENT_BACKEND`
(`langgraph`|`stub`), `LLM_PROVIDER` (`offline`|`openai`|`groq`), `LLM_MODEL`,
`MAX_TOOL_HOPS`, `OPENAI_API_KEY`/`GROQ_API_KEY` (server-side only),
`FLIGHT_API_PROVIDER` (`mock`|`airlabs`), `AIRLABS_API_KEY`, `FLIGHT_CACHE_TTL`,
`TTS_PROVIDER`, `CORS_ORIGINS`, `SESSION_TTL`.

Point `WHISPER_MODEL` at a local checkpoint dir instead of the HF Hub id if you
trained locally, e.g. `WHISPER_MODEL=../asr_finetuning/outputs/run/final`.

## Test

```bash
cd backend
pip install -r requirements-dev.txt
pytest                              # stub STT in tests (no GPU)
```

## Endpoints

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | — | status + `stt_loaded`, `whisper_model`, active backends |
| GET | `/airports` | — | installed `airport_id`s (KB-driven later) |
| POST | `/flight` | `{flight_number, airport_id?, position?}` | `{flight, route?}` — flight by number, scoped to airport (TDD-03) |
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
│   ├── config.py        # env-driven settings (.env auto-loaded)
│   ├── schemas.py       # pydantic request/response contracts
│   ├── sessions.py      # in-memory session store + TTL
│   ├── state.py         # process-wide service container
│   ├── routes.py        # REST + WebSocket, STT→agent→TTS orchestration
│   ├── agent/           # LangGraph agent (TDD-02): graph, providers/, tools/, prompts
│   └── services/        # stt / agent adapter / tts / flight, lang, audio_store
└── tests/               # TestClient end-to-end + test_agent.py (offline agent)
```

## STT integration (TDD-01)

The Darija fine-tune lives on the HF Hub as
[`Amassu/whisper-small-darija`](https://huggingface.co/Amassu/whisper-small-darija)
and is the default `WHISPER_MODEL`. `app/services/stt.py::WhisperSTT` wraps
`asr_finetuning`'s `WhisperTranscriber`.
