# syntax=docker/dockerfile:1
# Backend image (TDD-09): FastAPI + the full assistant stack, CPU-only.
# Heavy ML deps are installed so the FULL profile (fine-tuned Whisper STT, ChromaDB
# RAG, local MMS-TTS) works; the default compose runs the LIGHT profile (stubs) so
# it boots anywhere with no keys or model downloads. CPU torch keeps it CUDA-free.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/models

WORKDIR /app

# Audio libs for librosa/soundfile (STT) + curl for the healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libsndfile1 ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only torch first so nothing else pulls the multi-GB CUDA build.
RUN pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.1"

# Backend deps (incl. chromadb + sentence-transformers) + ASR-inference deps.
COPY backend/requirements.txt ./backend-req.txt
RUN pip install -r backend-req.txt transformers librosa soundfile

# App code. asr_finetuning is imported by WhisperSTT when LOAD_STT=true; stt.py
# resolves it at <repo>/asr_finetuning, so keep the same layout under /app.
COPY backend ./backend
COPY asr_finetuning ./asr_finetuning

WORKDIR /app/backend
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s \
    CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
