"""Ephemeral in-memory audio store so /converse can hand back an `audio_url`.

The TTS step produces bytes; we stash them under a short id and serve them from
GET /audio/{id}. Entries expire so memory stays bounded. A real deployment may
write to object storage instead.
"""

from __future__ import annotations

import time
import uuid

_MAX_AGE_SECONDS = 600


class AudioStore:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, bytes, str]] = {}

    def _evict(self) -> None:
        now = time.time()
        stale = [
            k for k, (ts, _, _) in self._items.items() if now - ts > _MAX_AGE_SECONDS
        ]
        for k in stale:
            del self._items[k]

    def put(self, audio: bytes, content_type: str) -> str:
        self._evict()
        audio_id = uuid.uuid4().hex
        self._items[audio_id] = (time.time(), audio, content_type)
        return audio_id

    def get(self, audio_id: str) -> tuple[bytes, str] | None:
        item = self._items.get(audio_id)
        if item is None:
            return None
        _, audio, content_type = item
        return audio, content_type


store = AudioStore()
