"""Integration test for the real STT path (TDD-06 ↔ TDD-01 wiring).

Verifies that with LOAD_STT=true the backend builds WhisperSTT and routes audio
through asr_finetuning's WhisperTranscriber — without downloading the model or
importing torch, by monkeypatching the two heavy seams in app.services.stt.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import stt as stt_module


class _FakeTranscriber:
    def __init__(self, model_name, language="arabic"):
        self.model_name = model_name
        self.language = language

    def transcribe(self, audio, sampling_rate=16000):
        return "بغيت نمشي للبوابة"


@pytest.fixture
def whisper_backend(monkeypatch):
    # Force the real STT branch, but stub the heavy bits (model load + decode).
    monkeypatch.setattr(settings, "load_stt", True)
    monkeypatch.setattr(
        stt_module,
        "_load_transcriber",
        lambda model_name, language: _FakeTranscriber(model_name, language),
    )
    monkeypatch.setattr(stt_module, "_decode_audio", lambda audio: [0.0, 0.0, 0.0])


def test_build_stt_selects_whisper_when_enabled(whisper_backend):
    svc = stt_module.build_stt()
    assert isinstance(svc, stt_module.WhisperSTT)
    assert svc.loaded is True
    # The adapter loads exactly the configured (fine-tuned) model id.
    assert svc._tr.model_name == settings.whisper_model


def test_transcribe_endpoint_uses_fine_tuned_whisper(whisper_backend):
    with TestClient(app) as c:
        r = c.post(
            "/transcribe",
            files={"audio": ("clip.wav", io.BytesIO(b"RIFFFAKE"), "audio/wav")},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "بغيت نمشي للبوابة"
    assert body["language"] == "ar"  # detect_language on Arabic script


def test_health_reports_stt_loaded(whisper_backend):
    with TestClient(app) as c:
        r = c.get("/health")
    body = r.json()
    assert body["stt_loaded"] is True
    assert body["whisper_model"] == settings.whisper_model


def test_transcribe_returns_400_on_undecodable_audio(whisper_backend, monkeypatch):
    # Browser uploads (webm) the decoder can't read should be a clean 400, not 500.
    def _boom(audio):
        raise stt_module.AudioDecodeError("Format not recognised")

    monkeypatch.setattr(stt_module, "_decode_audio", _boom)
    with TestClient(app) as c:
        r = c.post(
            "/transcribe",
            files={"audio": ("clip.webm", io.BytesIO(b"not-audio"), "audio/webm")},
        )
    assert r.status_code == 400
    assert "decode" in r.json()["detail"].lower()
