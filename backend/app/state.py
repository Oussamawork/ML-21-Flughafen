"""Process-wide service container, built once at app startup (lifespan).

Services are heavy/stateful (a model may load), so we build them once and share
them across requests rather than per-request.
"""

from __future__ import annotations

from .services.agent import Agent, build_agent
from .services.stt import STT, build_stt
from .services.tts import TTS, build_tts


class Services:
    stt: STT
    agent: Agent
    tts: TTS

    def __init__(self) -> None:
        self.stt = build_stt()
        self.agent = build_agent()
        self.tts = build_tts()

    @property
    def stt_loaded(self) -> bool:
        return getattr(self.stt, "loaded", False)


# Populated in the FastAPI lifespan handler (see main.py).
services: Services | None = None


def get_services() -> Services:
    if services is None:  # pragma: no cover - guards misuse outside lifespan
        raise RuntimeError("Services not initialised; app lifespan did not run.")
    return services
