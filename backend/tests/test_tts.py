"""TTS tests (TDD-05). The MMS engine is faked so pytest downloads no model;
real synthesis is covered by the live smoke check, not the suite.
"""

from __future__ import annotations

import types

import torch

import pytest

from app.config import settings
from app.services.tts import ElevenLabsTTS, MmsTTS, StubTTS, _speech_text, build_tts


class _FakeTokenizer:
    def __call__(self, text, return_tensors=None):
        return {}


class _FakeModel:
    def __init__(self):
        self.config = types.SimpleNamespace(sampling_rate=16000)
        self.calls = 0

    def eval(self):
        return self

    def __call__(self, **_kw):
        self.calls += 1
        return types.SimpleNamespace(waveform=torch.zeros(1, 8000))


def _provider_with_fakes():
    prov = MmsTTS()
    model = _FakeModel()
    fake = (_FakeTokenizer(), model)
    # Pre-load every configured model id so synthesize never imports transformers.
    for mid in set(prov._models.values()):
        prov._loaded[mid] = fake
    return prov, model


def test_speech_text_strips_markdown_around_codes():
    # `**B15**` was spoken as nothing — the voice must read the bare code.
    src = "البوابة هي **B15** في الطرمينال **A**. الرحلة `EY102`."
    out = _speech_text(src)
    assert "**" not in out and "`" not in out
    assert "B15" in out and "A" in out and "EY102" in out


def test_synthesize_returns_valid_wav():
    prov, _ = _provider_with_fakes()
    audio, content_type = prov.synthesize("Your gate is B12", "en")
    assert content_type == "audio/wav"
    assert audio[:4] == b"RIFF" and audio[8:12] == b"WAVE"


def test_darija_falls_back_to_arabic_voice():
    prov = MmsTTS()
    assert prov._models["ary"] == prov._models["ar"] == "facebook/mms-tts-ara"


def test_empty_text_is_silent_and_skips_model():
    prov, model = _provider_with_fakes()
    audio, content_type = prov.synthesize("   ", "en")
    assert content_type == "audio/wav" and audio[:4] == b"RIFF"
    assert model.calls == 0  # no synthesis for empty input


def test_phrase_cache_avoids_recompute():
    prov, model = _provider_with_fakes()
    prov.synthesize("hello", "en")
    prov.synthesize("hello", "en")
    assert model.calls == 1  # second call served from cache


def test_build_tts_dispatch(monkeypatch):
    monkeypatch.setattr(settings, "tts_provider", "local")
    assert isinstance(build_tts(), MmsTTS)
    monkeypatch.setattr(settings, "tts_provider", "stub")
    assert isinstance(build_tts(), StubTTS)


def test_elevenlabs_requires_key():
    with pytest.raises(RuntimeError):
        ElevenLabsTTS("", "voice", "model")


def test_elevenlabs_degrades_on_api_error():
    el = ElevenLabsTTS("k", "voice", "model", fallback=StubTTS())
    el._fetch = lambda _text: (_ for _ in ()).throw(RuntimeError("quota"))
    audio, content_type = el.synthesize("Your gate is B12", "en")
    assert content_type == "audio/wav" and audio[:4] == b"RIFF"  # stub fallback
