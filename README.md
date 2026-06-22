# ML-21-Flughafen — Multilingual Smart Airport Wayfinding Assistant

An agentic, voice + text assistant that guides airport passengers in
**Arabic / Darija / French / English** (case study: **Zayed International Airport, AUH**).

**Pipeline:** Next.js frontend → FastAPI backend orchestrating **STT (fine-tuned
Whisper)** → **LLM agent (LangGraph)** → **tools (AirLabs flight API) / RAG knowledge
base (ChromaDB)** → **TTS (local MMS-TTS)** → response.

The graded ML contribution is the **fine-tuned Whisper** model for Darija/Arabic
(`asr_finetuning/`, WER 108→28.8%). The LLM, TTS, and flight data are external
infrastructure by design. See [`docs/PROGRESS.md`](docs/PROGRESS.md) for the live
status board and [`docs/tdd/`](docs/tdd) for the Technical Design Documents.

## Run with Docker (recommended)

Needs Docker Desktop running. From the repo root:

```bash
# LIGHT profile — boots anywhere, no API keys, no model downloads
# (stub STT/TTS, offline LLM, keyword KB, mock flights):
docker compose -f deploy/docker-compose.yml up --build
```

- Frontend → http://localhost:3000 · Backend → http://localhost:8000/docs
- Health check: `curl localhost:8000/health`

### Full profile (the real stack)

The real assistant — **fine-tuned Whisper STT + ChromaDB multilingual RAG + local
MMS-TTS + live flight/LLM providers**. Put your keys in `backend/.env` (copy from
[`backend/.env.example`](backend/.env.example)), then:

```bash
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.full.yml up --build
docker compose exec backend python -m app.kb.ingest --all   # build the RAG store (once)
```

First run downloads the models (~2 GB) into the `models` volume, so boot is slower.

## Run locally (without Docker)

```bash
# Backend (Python 3.13+; ML deps optional unless using the full stack)
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # + ../asr_finetuning/requirements.txt for real STT
cp .env.example .env
uvicorn app.main:app --reload            # http://127.0.0.1:8000

# Frontend (Node 20+), in another shell
cd frontend && npm install && npm run dev # http://localhost:3000
```

## Test & evaluate

```bash
cd backend && pytest                      # end-to-end tests (offline stubs)
python evaluation/run_eval.py             # system evaluation report (TDD-08)
```

## Deploy to a PaaS (Railway / Render)

The images are PaaS-ready. Create **two services** from this repo:
- **backend** → Dockerfile `backend/Dockerfile`, port `8000`, healthcheck `/health`,
  a persistent volume mounted at `/models` (and `/app/backend/.kb_chroma`), and the
  env from `backend/.env.example` (set secrets in the PaaS secret store, never commit).
- **frontend** → Dockerfile `frontend/Dockerfile`, port `3000`, build arg
  `NEXT_PUBLIC_API_BASE_URL` = the backend's public URL.

Note: PaaS instances are usually CPU-only — the fine-tuned Whisper runs on CPU
(higher latency) or you can run the LIGHT profile for the hosted demo and keep the
full STT for the local/video demo. CI (`.github/workflows/ci.yml`) runs backend
tests + the frontend build on every PR.

## Repository layout

| Path | What |
|---|---|
| `asr_finetuning/` | Fine-tuned Whisper (TDD-01) — the owned ML model |
| `backend/` | FastAPI service: agent (`app/agent/`), KB+RAG (`app/kb/`), services (TDD-02–06) |
| `frontend/` | Next.js dashboard (TDD-07) |
| `evaluation/` | Reproducible system evaluation (TDD-08) |
| `deploy/` | Docker Compose (TDD-09) |
| `docs/` | TDDs + progress board |
