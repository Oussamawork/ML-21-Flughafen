"""End-to-end API tests against the stub services (no GPU / no external APIs).

Run from the backend/ directory:  pytest
"""

from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _fake_wav() -> bytes:
    return b"RIFFFAKEWAVEdata" + b"\x00" * 16


def test_health():
    with TestClient(app) as c:
        r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["stt_loaded"] is False  # conftest forces stub STT for tests
    assert "version" in body


def test_airports():
    with TestClient(app) as c:
        r = c.get("/airports")
    assert r.status_code == 200
    body = r.json()
    assert body["default"] in body["airports"]


def test_chat_detects_flight_and_gate():
    with TestClient(app) as c:
        r = c.post("/chat", json={"text": "where is my gate for flight SV-624?"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "find_gate"
    assert "B12" in body["answer"]  # mock flight data
    assert body["tool_trace"][0]["tool"] == "flight_status"
    assert body["session_id"]
    assert "agent" in body["latency_ms"]


def test_chat_uses_typed_flight_number():
    # The dashboard sends the ticket-strip number; the question need not repeat it.
    with TestClient(app) as c:
        r = c.post("/chat", json={"text": "where is my gate?", "flight_number": "SV624"})
    body = r.json()
    assert body["intent"] == "find_gate"
    assert "B12" in body["answer"]
    assert body["tool_trace"][0]["args"]["flight_number"] == "SV624"


def test_chat_remembers_flight_number_across_turns():
    # Once set, the typed number persists on the session for later turns.
    with TestClient(app) as c:
        first = c.post("/chat", json={"text": "gate?", "flight_number": "SV624"}).json()
        sid = first["session_id"]
        second = c.post("/chat", json={"text": "and the terminal?", "session_id": sid}).json()
    assert second["tool_trace"][0]["args"]["flight_number"] == "SV624"


def test_chat_unknown_flight():
    with TestClient(app) as c:
        r = c.post("/chat", json={"text": "status of flight ZZ999"})
    assert r.status_code == 200
    assert r.json()["intent"] == "find_gate"


def test_chat_language_french():
    with TestClient(app) as c:
        r = c.post("/chat", json={"text": "où est la pharmacie la plus proche"})
    assert r.json()["language"] == "fr"


def test_chat_empty_text_rejected():
    with TestClient(app) as c:
        r = c.post("/chat", json={"text": ""})
    assert r.status_code == 422


def test_session_continuity():
    with TestClient(app) as c:
        first = c.post("/chat", json={"text": "hello"}).json()
        sid = first["session_id"]
        second = c.post("/chat", json={"text": "SV624", "session_id": sid}).json()
    assert second["session_id"] == sid


def test_transcribe_stub():
    with TestClient(app) as c:
        r = c.post(
            "/transcribe",
            files={"audio": ("clip.wav", io.BytesIO(_fake_wav()), "audio/wav")},
        )
    assert r.status_code == 200
    assert r.json()["text"]  # stub returns a placeholder transcript


def test_speak_returns_audio():
    with TestClient(app) as c:
        r = c.post("/speak", json={"text": "hello", "language": "en"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("audio/")
    assert r.content[:4] == b"RIFF"  # WAV header


def test_converse_full_pipeline():
    with TestClient(app) as c:
        r = c.post(
            "/converse",
            files={"audio": ("clip.wav", io.BytesIO(_fake_wav()), "audio/wav")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["text_in"]
        assert body["answer"]
        assert body["audio_url"].startswith("/audio/")
        # the produced audio is retrievable
        audio = c.get(body["audio_url"])
    assert audio.status_code == 200
    assert audio.content[:4] == b"RIFF"


def test_websocket_text_turn():
    with TestClient(app) as c:
        with c.websocket_connect("/ws/test-session") as ws:
            ws.send_json({"type": "text", "data": "flight SV624"})
            reply = ws.receive_json()
    assert reply["type"] == "answer"
    assert "B12" in reply["answer"]
