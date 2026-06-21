"""FastAPI application entry point (TDD-06).

Run locally:
    cd backend
    uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, state
from .config import settings
from .routes import router
from .state import Services


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build services once (loads the fine-tuned Whisper STT by default).
    state.services = Services()
    yield
    state.services = None


app = FastAPI(
    title="Smart Airport Wayfinding Assistant — Backend",
    version=__version__,
    summary="Voice/text airport assistant API: STT -> agent -> TTS.",
    lifespan=lifespan,
)

# Credentials cannot be combined with a wildcard origin (the browser rejects it,
# and Starlette would otherwise reflect any Origin). Only allow credentials when
# explicit origins are configured.
_allow_credentials = "*" not in settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict:
    return {"service": "wayfinding-backend", "version": __version__, "docs": "/docs"}
