"""Text-to-Speech service (TDD-05).

Interface: `synthesize(text, language) -> (audio_bytes, content_type)`.

- `MmsTTS` (default): real **local** neural TTS via Meta MMS-TTS
  (`facebook/mms-tts-*`) on the already-installed `transformers`/`torch` stack —
  no API key, fully offline (same philosophy as the fine-tuned Whisper, TDD-01).
  One model per language, lazy-loaded + cached; Darija (`ary`) uses the Arabic
  voice (documented limitation). Returns 16 kHz mono PCM WAV.
- `ElevenLabsTTS` (`TTS_PROVIDER=elevenlabs`): hosted neural voices — natural and
  reads gate codes/numbers correctly (MMS drops embedded Latin/digits). Needs a key;
  falls back to local MMS on error so the round-trip never breaks.
- `StubTTS`: a short silent WAV — used by the test suite (`TTS_PROVIDER=stub`) so
  no model is downloaded.
"""

from __future__ import annotations

import logging
import os
import re
import struct
from typing import Protocol

from ..config import settings

logger = logging.getLogger(__name__)

_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")  # [text](url) -> text


def _speech_text(text: str) -> str:
    """Strip markdown so the voice reads clean prose, not `**`/`*`/`` ` ``/`#`
    around gate codes and numbers (e.g. `**B15**` was spoken as nothing)."""
    text = _MD_LINK.sub(r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "").replace("~~", "")
    text = re.sub(r"(?<!\w)[*_](?=\S)", "", text)  # opening * / _ emphasis
    text = re.sub(r"(?<=\S)[*_](?!\w)", "", text)  # closing * / _ emphasis
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.MULTILINE)  # headings
    return text


def _silent_wav(duration_s: float = 0.4, sample_rate: int = 16000) -> bytes:
    """Build a minimal valid mono 16-bit PCM WAV of silence."""
    n_samples = int(duration_s * sample_rate)
    return _wrap_wav(b"\x00\x00" * n_samples, sample_rate)


def _wrap_wav(pcm: bytes, sample_rate: int) -> bytes:
    """Wrap raw 16-bit mono PCM bytes in a WAV container."""
    byte_rate = sample_rate * 2
    header = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, byte_rate, 2, 16)
    header += b"data" + struct.pack("<I", len(pcm))
    return header + pcm


def _float_to_wav(waveform, sample_rate: int) -> bytes:
    """Convert a float waveform in [-1, 1] to a 16-bit mono PCM WAV."""
    import numpy as np

    samples = np.asarray(waveform, dtype=np.float32).flatten()
    pcm = (np.clip(samples, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    return _wrap_wav(pcm, sample_rate)


class TTS(Protocol):
    def synthesize(self, text: str, language: str) -> tuple[bytes, str]: ...


class StubTTS:
    def synthesize(self, text: str, language: str) -> tuple[bytes, str]:
        # Duration loosely scaled to text length so clips feel proportional.
        duration = min(5.0, max(0.4, len(text) * 0.06))
        return _silent_wav(duration), "audio/wav"


# Language -> MMS model id. Darija (ary) uses the Arabic voice (no dedicated Darija
# TTS); overridable per language via TTS_MODEL_<LANG> (e.g. TTS_MODEL_AR).
_DEFAULT_MODELS = {
    "ar": "facebook/mms-tts-ara",
    "ary": "facebook/mms-tts-ara",
    "fr": "facebook/mms-tts-fra",
    "en": "facebook/mms-tts-eng",
}


class MmsTTS:
    """Local MMS-TTS. Models load lazily on first use of each language and are
    cached for the process; a small phrase cache makes replays instant."""

    def __init__(self, models: dict[str, str] | None = None, max_chars: int = 600) -> None:
        base = dict(models or _DEFAULT_MODELS)
        for lang in list(base):
            base[lang] = os.getenv(f"TTS_MODEL_{lang.upper()}", base[lang])
        self._models = base
        self._max_chars = max_chars
        self._loaded: dict[str, tuple] = {}          # model_id -> (tokenizer, model)
        self._cache: dict[tuple[str, str], bytes] = {}  # (model_id, text) -> wav

    def _engine(self, model_id: str):
        eng = self._loaded.get(model_id)
        if eng is None:
            from transformers import AutoTokenizer, VitsModel

            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = VitsModel.from_pretrained(model_id)
            model.eval()
            eng = (tokenizer, model)
            self._loaded[model_id] = eng
        return eng

    def synthesize(self, text: str, language: str) -> tuple[bytes, str]:
        text = _speech_text(text or "").strip()
        if not text:
            return _silent_wav(0.2), "audio/wav"
        model_id = self._models.get(language, self._models["en"])
        clipped = text[: self._max_chars]
        key = (model_id, clipped)
        cached = self._cache.get(key)
        if cached is not None:
            return cached, "audio/wav"

        import torch

        tokenizer, model = self._engine(model_id)
        inputs = tokenizer(clipped, return_tensors="pt")
        with torch.no_grad():
            waveform = model(**inputs).waveform
        wav = _float_to_wav(waveform[0].cpu().numpy(), model.config.sampling_rate)
        if len(self._cache) < 256:  # bounded phrase cache
            self._cache[key] = wav
        return wav, "audio/wav"


class ElevenLabsTTS:
    """Hosted ElevenLabs TTS — natural multilingual voice that reads gate codes and
    numbers correctly. Returns MP3. Phrase-cached (free tier is char-limited); on any
    API error it degrades to the local `fallback` so /speak never crashes."""

    _BASE = "https://api.elevenlabs.io/v1/text-to-speech"

    def __init__(self, api_key: str, voice_id: str, model: str,
                 fallback: TTS | None = None, max_chars: int = 900) -> None:
        if not api_key:
            raise RuntimeError("ELEVENLABS_API_KEY required for TTS_PROVIDER=elevenlabs")
        self._key = api_key
        self._voice = voice_id
        self._model = model
        self._fallback = fallback or StubTTS()
        self._max_chars = max_chars
        self._cache: dict[str, bytes] = {}

    def _fetch(self, text: str) -> bytes:
        import json
        import urllib.request

        body = json.dumps({
            "text": text,
            "model_id": self._model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            "apply_text_normalization": "on",  # spell out gate codes/digits (e.g. B15, 19:19)
        }).encode()
        req = urllib.request.Request(
            f"{self._BASE}/{self._voice}", data=body, method="POST",
            headers={"xi-api-key": self._key, "content-type": "application/json",
                     "accept": "audio/mpeg"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()

    def synthesize(self, text: str, language: str) -> tuple[bytes, str]:
        text = _speech_text(text or "").strip()
        if not text:
            return _silent_wav(0.2), "audio/wav"
        clipped = text[: self._max_chars]
        cached = self._cache.get(clipped)
        if cached is not None:
            return cached, "audio/mpeg"
        try:
            audio = self._fetch(clipped)
        except Exception as exc:  # quota/network/bad-key -> degrade to local voice
            logger.warning("ElevenLabs TTS failed (%s); falling back to local voice", exc)
            return self._fallback.synthesize(text, language)
        if len(self._cache) < 256:
            self._cache[clipped] = audio
        return audio, "audio/mpeg"


def build_tts() -> TTS:
    """`local`/`mms` -> local MMS-TTS (default); `elevenlabs` -> hosted neural voice
    (falls back to local MMS); `stub` -> silent WAV (tests). Unknown -> stub so the
    API never fails to start."""
    if settings.tts_provider == "elevenlabs":
        return ElevenLabsTTS(
            settings.elevenlabs_api_key,
            settings.elevenlabs_voice_id,
            settings.elevenlabs_model,
            fallback=MmsTTS(),
        )
    if settings.tts_provider in ("local", "mms"):
        return MmsTTS()
    return StubTTS()
