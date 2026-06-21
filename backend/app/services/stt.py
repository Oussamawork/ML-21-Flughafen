"""Speech-to-Text service (TDD-01 integration point).

Interface: `transcribe(audio_bytes, filename) -> (text, language)`.

- `StubSTT` (default): no model, returns a placeholder so the API runs offline.
- `WhisperSTT`: lazily wraps `asr_finetuning`'s `WhisperTranscriber` when
  `LOAD_STT=true` and a model path/id is configured. Importing torch is deferred
  to that path so the backend boots without it.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Protocol

from ..config import settings
from .lang import detect_language


class STT(Protocol):
    def transcribe(
        self, audio: bytes, filename: str | None = None
    ) -> tuple[str, str]: ...


class StubSTT:
    """Offline placeholder. Does not look at the audio bytes."""

    loaded = False

    def transcribe(self, audio: bytes, filename: str | None = None) -> tuple[str, str]:
        # A fixed Darija sample so downstream stages have realistic input to work
        # with during development. Replace by enabling the real model (LOAD_STT).
        text = "أين بوابتي، رحلتي SV-624"
        return text, detect_language(text)


_TARGET_SR = 16000


def _load_transcriber(model_name: str, language: str):
    """Build the heavy WhisperTranscriber; isolated so tests can monkeypatch it."""
    import sys

    asr_dir = Path(__file__).resolve().parents[3] / "asr_finetuning"
    if str(asr_dir) not in sys.path:
        sys.path.insert(0, str(asr_dir))
    from src.transcribe import WhisperTranscriber  # noqa: E402 (lazy, heavy)

    return WhisperTranscriber(model_name, language=language)


class AudioDecodeError(Exception):
    """Raised when uploaded audio bytes can't be decoded (bad/unsupported format)."""


def _decode_audio(audio: bytes):
    """Decode arbitrary uploaded audio bytes to a 16 kHz mono float array."""
    import librosa

    try:
        array, _ = librosa.load(io.BytesIO(audio), sr=_TARGET_SR, mono=True)
    except Exception as exc:  # soundfile/audioread raise various types
        raise AudioDecodeError(str(exc)) from exc
    return array


class WhisperSTT:
    """Adapter over the fine-tuned Whisper served by asr_finetuning.

    Loads `settings.whisper_model` once (default: the DODa fine-tune on the HF
    Hub). Heavy imports (torch/transformers/librosa) live in module helpers so
    the rest of the backend stays import-light.
    """

    loaded = True

    def __init__(self) -> None:
        self._tr = _load_transcriber(settings.whisper_model, settings.whisper_language)

    def transcribe(self, audio: bytes, filename: str | None = None) -> tuple[str, str]:
        array = _decode_audio(audio)
        text = self._tr.transcribe(array, sampling_rate=_TARGET_SR)
        return text, detect_language(text)


def build_stt() -> STT:
    if settings.load_stt:
        return WhisperSTT()
    return StubSTT()
