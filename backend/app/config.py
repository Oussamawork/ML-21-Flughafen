"""Runtime configuration, read from environment variables.

Kept dependency-light (plain os.environ) so the backend imports without extra
packages. Every external provider and model path is configurable — never a
literal — per the TDD-00 "config over code" rule.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env before reading settings (copy from .env.example).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


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
    # When false, a stub STT is used (no GPU). Default true = fine-tuned Whisper.
    load_stt: bool = field(default_factory=lambda: _bool("LOAD_STT", True))
    # Default = the DODa Darija fine-tune on the HF Hub (TDD-01).
    whisper_model: str = field(
        default_factory=lambda: os.getenv("WHISPER_MODEL", "Amassu/whisper-small-darija")
    )
    whisper_language: str = field(
        default_factory=lambda: os.getenv("WHISPER_LANGUAGE", "arabic")
    )

    # --- agent (TDD-02) ---
    # "langgraph" = the LangGraph agent (default); "stub" = rule-based fallback.
    agent_backend: str = field(
        default_factory=lambda: os.getenv("AGENT_BACKEND", "langgraph")
    )
    # LLM behind a provider interface. "offline" (default) is deterministic and
    # needs no key; "openai"/"groq" are lazy-imported when selected + a key is set.
    llm_provider: str = field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "offline")
    )
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini")
    )
    max_tool_hops: int = field(
        default_factory=lambda: int(os.getenv("MAX_TOOL_HOPS", "4"))
    )
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    # --- flight data (TDD-03) ---
    # "mock" (default) = canned flights, no network/key. "airlabs" = real lookup.
    flight_api_provider: str = field(
        default_factory=lambda: os.getenv("FLIGHT_API_PROVIDER", "mock")
    )
    airlabs_api_key: str = field(
        default_factory=lambda: os.getenv("AIRLABS_API_KEY", "")
    )
    flight_cache_ttl: int = field(
        default_factory=lambda: int(os.getenv("FLIGHT_CACHE_TTL", "60"))
    )

    # --- tts (TDD-05) ---
    # "stub" returns silent audio; real providers: "elevenlabs" / "azure".
    tts_provider: str = field(default_factory=lambda: os.getenv("TTS_PROVIDER", "stub"))


settings = Settings()
