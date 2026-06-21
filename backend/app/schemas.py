"""Pydantic request/response models — the API's data contracts (TDD-06)."""

from __future__ import annotations

from pydantic import BaseModel, Field

# Language codes carried across the whole pipeline (TDD-00 cross-cutting rule).
Language = str  # one of: "ar", "ary" (Darija), "fr", "en"


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    stt_loaded: bool
    agent_backend: str
    tts_provider: str


class TranscribeResponse(BaseModel):
    text: str
    language: Language
    session_id: str


class ChatRequest(BaseModel):
    text: str = Field(..., min_length=1)
    session_id: str | None = None
    airport_id: str | None = None
    language: Language | None = None


class ToolCall(BaseModel):
    tool: str
    args: dict = Field(default_factory=dict)
    result: dict | None = None


class ChatResponse(BaseModel):
    answer: str
    language: Language
    intent: str
    tool_trace: list[ToolCall] = Field(default_factory=list)
    session_id: str
    latency_ms: dict[str, float] = Field(default_factory=dict)


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: Language = "en"


class ConverseResponse(BaseModel):
    text_in: str
    answer: str
    language: Language
    intent: str
    audio_url: str
    session_id: str
    tool_trace: list[ToolCall] = Field(default_factory=list)
    latency_ms: dict[str, float] = Field(default_factory=dict)


class AirportsResponse(BaseModel):
    airports: list[str]
    default: str
