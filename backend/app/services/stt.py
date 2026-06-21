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


class WhisperSTT:
    """Adapter over the fine-tuned Whisper served by asr_finetuning."""

    loaded = True

    def __init__(self) -> None:
        # Make `asr_finetuning` importable (its modules use the `src.` prefix).
        import sys

        asr_dir = Path(__file__).resolve().parents[3] / "asr_finetuning"
        if str(asr_dir) not in sys.path:
            sys.path.insert(0, str(asr_dir))
        from src.transcribe import WhisperTranscriber  # noqa: E402 (lazy, heavy)

        self._tr = WhisperTranscriber(
            settings.whisper_model, language=settings.whisper_language
        )

    def transcribe(self, audio: bytes, filename: str | None = None) -> tuple[str, str]:
        import librosa

        array, _ = librosa.load(io.BytesIO(audio), sr=16000, mono=True)
        text = self._tr.transcribe(array, sampling_rate=16000)
        return text, detect_language(text)


def build_stt() -> STT:
    if settings.load_stt:
        return WhisperSTT()
    return StubSTT()
