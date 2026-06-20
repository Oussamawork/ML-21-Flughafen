"""Text-to-Speech service (TDD-05 integration point).

Interface: `synthesize(text, language) -> (audio_bytes, content_type)`.

`StubTTS` returns a short **silent WAV** (valid audio the browser can play) so the
voice round-trip works without an external TTS provider. Real providers
(ElevenLabs/Azure) land in TDD-05 behind the same interface.
"""

from __future__ import annotations

import struct
from typing import Protocol



def _silent_wav(duration_s: float = 0.4, sample_rate: int = 16000) -> bytes:
    """Build a minimal valid mono 16-bit PCM WAV of silence."""
    n_samples = int(duration_s * sample_rate)
    data = b"\x00\x00" * n_samples
    byte_rate = sample_rate * 2
    header = b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, byte_rate, 2, 16)
    header += b"data" + struct.pack("<I", len(data))
    return header + data


class TTS(Protocol):
    def synthesize(self, text: str, language: str) -> tuple[bytes, str]: ...


class StubTTS:
    def synthesize(self, text: str, language: str) -> tuple[bytes, str]:
        # Duration loosely scaled to text length so clips feel proportional.
        duration = min(5.0, max(0.4, len(text) * 0.06))
        return _silent_wav(duration), "audio/wav"


def build_tts() -> TTS:
    # Only the stub exists today; TTS_PROVIDER reserved for elevenlabs/azure (TDD-05).
    return StubTTS()
