# TDD-09 — Deployment & DevOps

**Component:** `deploy/`
**Status:** 🟢 Built — `backend/Dockerfile` (CPU torch) + `frontend/Dockerfile`
(Next standalone) + `deploy/docker-compose.yml` (light default) +
`docker-compose.full.yml` (real stack) + root README setup/deploy + CI
(`.github/workflows/ci.yml`). Compose validated; image build/run is the user's
step (Docker daemon). Live PaaS deploy documented (needs the user's account).
**Depends on:** TDD-06 (backend), TDD-07 (frontend)

---

## 1. Purpose

Make the system reproducible and deployable: containerize the services, manage
configuration/secrets, and deploy to a PaaS for the live demo.

## 2. Requirements satisfied

- *Containerization: Docker, deployed on Railway or Render.*
- *README documenting the development environment setup* (submission deliverable).

## 3. Design

### 3.1 Containers
- `backend/Dockerfile` — Python 3.11, FastAPI + Uvicorn, installs `backend` +
  component deps. GPU optional (Whisper); CPU image for the hosted demo with the
  fine-tuned small model, or call a hosted STT if latency requires.
- `frontend/Dockerfile` — Node build → static/Next server.
- `docker-compose.yml` — local one-command bring-up (backend + frontend +
  ChromaDB persistent volume).

### 3.2 Configuration & secrets
- All config via env vars (`.env.example` committed, real `.env` git-ignored):
  `LLM_PROVIDER`, `OPENAI_API_KEY`/`GROQ_API_KEY`, `FLIGHT_API_PROVIDER` (=`airlabs`),
  `AIRLABS_API_KEY`, `FLIGHT_CACHE_TTL`, `TTS_PROVIDER`, `TTS_API_KEY`,
  `WHISPER_MODEL`, `LOAD_STT`, `KB_PERSIST_DIR`, `AIRPORT_ID` (default `AUH`).
- The fine-tuned Whisper checkpoint: pulled from HF Hub at boot or baked into the
  image (size trade-off documented).

### 3.3 Deployment targets
- **Railway / Render**: backend service + frontend service; ChromaDB as a
  persistent volume or managed alternative. Health check on `/health`.
- CI (optional, GitHub Actions): lint + tests on PR; build images on tag.

### 3.4 Environments
- **local** (compose, mock providers OK) → **demo** (PaaS, real keys).

## 4. Interfaces & artifacts

- `deploy/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`,
  `.env.example`, and a root `README.md` "Environment setup" section (required by
  the submission).

## 5. Dependencies

Docker, Docker Compose, Railway/Render account, HF Hub (model pull).

## 6. Open questions / risks

- **GPU on PaaS** — usually none/costly → run small Whisper on CPU (accept
  latency) or use a hosted STT *in the deployed demo only* while keeping the
  fine-tuned model as the documented contribution + local/video demo.
- **Image size** with torch + model weights → slim base, CPU-only torch wheel.
- **Secret management** on the PaaS (never commit keys).

## 7. Task checklist

- [x] `backend/Dockerfile` (CPU-only torch, full-capable) + `.dockerignore`
- [x] `frontend/Dockerfile` (multi-stage, Next `output: standalone`) + `.dockerignore`
- [x] `deploy/docker-compose.yml` (light default) + `docker-compose.full.yml`
      (real stack) — backend + frontend + `models`/`kb_chroma` volumes; `config` validated
- [x] Root `README.md` — Docker run (light/full), local dev, test/eval, PaaS deploy
- [x] GitHub Actions CI (`.github/workflows/ci.yml`) — backend pytest + frontend build
- [ ] **Live** Railway/Render deploy (needs the user's account; steps documented)
- Light/full profiles via env (`LOAD_STT`/`KB_RETRIEVER`/`TTS_PROVIDER`/...); HF
      weights cached in the `models` volume; secrets stay in `backend/.env` (gitignored)
