"""Runtime configuration, read from environment variables.

Kept dependency-light (plain os.environ) so the backend imports without extra
packages. Every external provider and model path is configurable — never a
literal — per the TDD-00 "config over code" rule.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: list[str]) -> list[str]:
    val = os.getenv(name)
    if not val:
        return default
    return [item.strip() for item in val.split(",") if item.strip()]


@dataclass
class Settings:
    # --- general ---
    default_airport_id: str = field(
        default_factory=lambda: os.getenv("AIRPORT_ID", "AUH")
    )
    session_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("SESSION_TTL", "1800"))
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _list("CORS_ORIGINS", ["*"])
    )

    # --- speech-to-text (TDD-01) ---
    # When false (default) a stub STT is used so the API boots without a GPU/model.
    load_stt: bool = field(default_factory=lambda: _bool("LOAD_STT", False))
    # Default = the DODa Darija fine-tune on the HF Hub (TDD-01).
    whisper_model: str = field(
        default_factory=lambda: os.getenv("WHISPER_MODEL", "Amassu/whisper-small-darija")
    )
    whisper_language: str = field(
        default_factory=lambda: os.getenv("WHISPER_LANGUAGE", "arabic")
    )

    # --- agent (TDD-02) ---
    # "stub" until the LangGraph agent lands; then "langgraph".
    agent_backend: str = field(
        default_factory=lambda: os.getenv("AGENT_BACKEND", "stub")
    )

    # --- tts (TDD-05) ---
    # "stub" returns silent audio; real providers: "elevenlabs" / "azure".
    tts_provider: str = field(default_factory=lambda: os.getenv("TTS_PROVIDER", "stub"))


settings = Settings()
