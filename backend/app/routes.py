"""HTTP + WebSocket routes orchestrating STT -> agent -> TTS (TDD-06)."""

from __future__ import annotations

import base64
import logging
import time
from contextlib import contextmanager

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.responses import Response
from starlette.websockets import WebSocketDisconnect

from . import __version__
from .config import settings
from .schemas import (
    AirportsResponse,
    ChatRequest,
    ChatResponse,
    ConverseResponse,
    FlightInfo,
    FlightRequest,
    FlightResponse,
    HealthResponse,
    SpeakRequest,
    ToolCall,
    TranscribeResponse,
)
from .services import audio_store
from .services.flight import FlightUnavailable
from .services.stt import AudioDecodeError
from .sessions import store as session_store
from .state import get_services

logger = logging.getLogger(__name__)

router = APIRouter()


@contextmanager
def _timed(bucket: dict[str, float], name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        bucket[name] = round((time.perf_counter() - start) * 1000, 1)


def _run_agent_turn(
    text: str,
    session,
    language: str | None,
    flight_number: str | None = None,
    position: str | None = None,
) -> ChatResponse:
    """Shared agent step used by /chat, /converse and the WebSocket.

    Typed `flight_number`/`position` (from the dashboard) are remembered on the
    session so later turns — including voice — stay grounded without resending.
    """
    services = get_services()
    latency: dict[str, float] = {}
    if flight_number:
        session.flight_number = flight_number
    if position:
        session.position = position
    session.add("user", text)
    with _timed(latency, "agent"):
        reply = services.agent.run(
            text=text,
            language=language or session.language,
            airport_id=session.airport_id,
            history=session.messages,
            flight_number=session.flight_number,
            position=session.position,
        )
    session.language = reply.language
    session.add("assistant", reply.answer)
    return ChatResponse(
        answer=reply.answer,
        language=reply.language,
        intent=reply.intent,
        tool_trace=[ToolCall(**tc) for tc in reply.tool_trace],
        session_id=session.session_id,
        latency_ms=latency,
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    services = get_services()
    return HealthResponse(
        version=__version__,
        stt_loaded=services.stt_loaded,
        whisper_model=settings.whisper_model if services.stt_loaded else None,
        agent_backend=settings.agent_backend,
        tts_provider=settings.tts_provider,
    )


@router.get("/airports", response_model=AirportsResponse)
def airports() -> AirportsResponse:
    # Until the KB (TDD-04) lists installed airport packs, expose the configured one.
    return AirportsResponse(
        airports=[settings.default_airport_id], default=settings.default_airport_id
    )


@router.post("/flight", response_model=FlightResponse)
def flight(req: FlightRequest) -> FlightResponse:
    """Look up a flight by its (typed) number, scoped to airport_id (default AUH).

    Powers the ticket-first dashboard. `route` is reserved for the KB map (TDD-04).
    """
    services = get_services()
    airport_id = req.airport_id or settings.default_airport_id
    try:
        info = services.flight.get_flight(req.flight_number, airport_id)
    except FlightUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Flight data unavailable: {exc}")
    if info is None:
        raise HTTPException(status_code=404, detail="Flight not found.")
    return FlightResponse(flight=FlightInfo(**info))


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(...), session_id: str | None = Form(default=None)
) -> TranscribeResponse:
    services = get_services()
    raw = await audio.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty audio upload.")
    try:
        text, language = services.stt.transcribe(raw, audio.filename)
    except AudioDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode audio: {exc}")
    session = session_store.get_or_create(session_id)
    session.language = language
    return TranscribeResponse(
        text=text, language=language, session_id=session.session_id
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    session = session_store.get_or_create(req.session_id, req.airport_id)
    return _run_agent_turn(
        req.text, session, req.language, req.flight_number, req.position
    )


@router.post("/speak")
def speak(req: SpeakRequest) -> Response:
    services = get_services()
    audio, content_type = services.tts.synthesize(req.text, req.language)
    return Response(content=audio, media_type=content_type)


@router.post("/converse", response_model=ConverseResponse)
async def converse(
    audio: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    flight_number: str | None = Form(default=None),
    position: str | None = Form(default=None),
) -> ConverseResponse:
    """One-shot voice pipeline: STT -> agent -> TTS, with per-stage timings."""
    services = get_services()
    latency: dict[str, float] = {}

    raw = await audio.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty audio upload.")

    try:
        with _timed(latency, "stt"):
            text_in, language = services.stt.transcribe(raw, audio.filename)
    except AudioDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Could not decode audio: {exc}")

    session = session_store.get_or_create(session_id)
    chat_resp = _run_agent_turn(text_in, session, language, flight_number, position)
    latency.update(chat_resp.latency_ms)

    with _timed(latency, "tts"):
        clip, content_type = services.tts.synthesize(
            chat_resp.answer, chat_resp.language
        )
    audio_id = audio_store.store.put(clip, content_type)

    return ConverseResponse(
        text_in=text_in,
        answer=chat_resp.answer,
        language=chat_resp.language,
        intent=chat_resp.intent,
        audio_url=f"/audio/{audio_id}",
        session_id=session.session_id,
        tool_trace=chat_resp.tool_trace,
        latency_ms=latency,
    )


@router.get("/audio/{audio_id}")
def get_audio(audio_id: str) -> Response:
    item = audio_store.store.get(audio_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Audio not found or expired.")
    audio, content_type = item
    return Response(content=audio, media_type=content_type)


@router.websocket("/ws/{session_id}")
async def ws(websocket: WebSocket, session_id: str) -> None:
    """Turn-based real-time channel. Client sends {type:'text'|'audio', ...}."""
    await websocket.accept()
    services = get_services()
    session = session_store.get_or_create(session_id)
    try:
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")
            if mtype == "text":
                text = msg.get("data", "")
            elif mtype == "audio":
                raw = base64.b64decode(msg.get("data", ""))
                text, _ = services.stt.transcribe(raw)
                await websocket.send_json({"type": "transcript", "text": text})
            else:
                await websocket.send_json({"type": "error", "detail": "unknown type"})
                continue

            resp = _run_agent_turn(
                text, session, msg.get("language"),
                msg.get("flight_number"), msg.get("position"),
            )
            await websocket.send_json({"type": "answer", **resp.model_dump()})
    except WebSocketDisconnect:
        return  # normal client disconnect ends the loop
    except Exception:
        # A real bug (not a disconnect): log it and close cleanly so it surfaces.
        logger.exception("WebSocket handler failed for session %s", session_id)
        await websocket.close(code=1011)
