"""Pydantic request/response models — the API's data contracts (TDD-06)."""

from __future__ import annotations

from pydantic import BaseModel, Field

# Language codes carried across the whole pipeline (TDD-00 cross-cutting rule).
Language = str  # one of: "ar", "ary" (Darija), "fr", "en"


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    stt_loaded: bool
    whisper_model: str | None = None  # set when the real Whisper STT is active
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
    flight_number: str | None = None  # typed in the ticket strip (TDD-00), not from STT
    position: str | None = None       # current map node (TDD-04)


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


class FlightRequest(BaseModel):
    flight_number: str = Field(..., min_length=2)
    airport_id: str | None = None
    position: str | None = None  # reserved for route (TDD-04 map)


class FlightInfo(BaseModel):
    flight_number: str
    airline: str | None = None
    status: str | None = None
    direction: str | None = None  # departure | arrival | other
    scheduled: str | None = None
    estimated: str | None = None
    actual: str | None = None
    gate: str | None = None
    terminal: str | None = None
    baggage: str | None = None  # arrivals only (AirLabs arr_baggage)
    delay_minutes: int | None = None
    departure_airport: str | None = None
    arrival_airport: str | None = None
    aircraft: str | None = None
    source: str


class FlightResponse(BaseModel):
    flight: FlightInfo
    route: dict | None = None  # KB route entrance/position -> the flight's gate (TDD-04)
    checkin: dict | None = None  # KB check-in desk/zone (AirLabs has none) (TDD-04)


class MapRequest(BaseModel):
    airport_id: str | None = None
    flight_number: str | None = None  # route to this flight's gate (typed; TDD-00)
    gate: str | None = None           # or route directly to a gate code
    to_node: str | None = None        # or to an explicit layout node
    position: str | None = None       # "I am here" origin node


class MapResponse(BaseModel):
    airport_id: str
    nodes: dict = Field(default_factory=dict)         # node id -> display name
    positions: dict = Field(default_factory=dict)     # node id -> {x, y} (% coords)
    zones: list = Field(default_factory=list)         # labelled rectangles
    route: list[str] = Field(default_factory=list)    # ordered node ids (the polyline)
    route_summary: dict | None = None                 # {distance_m, walking_time_min, steps}
    current_position: str | None = None
    to_node: str | None = None
    gate_label: str | None = None                     # real gate code at the target (e.g. C33)
