"""TTS tests (TDD-05). The MMS engine is faked so pytest downloads no model;
real synthesis is covered by the live smoke check, not the suite.
"""

from __future__ import annotations

import types

import torch

from app.config import settings
from app.services.tts import MmsTTS, StubTTS, build_tts


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
