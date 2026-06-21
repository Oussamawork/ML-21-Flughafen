"""In-memory session store with TTL eviction (TDD-06 §3.4).

Stateless services; the session (history, language, airport) lives here keyed by
session_id. Swappable for Redis later behind the same small interface.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from .config import settings


@dataclass
class Session:
    session_id: str
    airport_id: str
    language: str | None = None
    messages: list[dict] = field(default_factory=list)  # {role, content}
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.last_access = time.time()

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})


class SessionStore:
    def __init__(self, ttl_seconds: int | None = None) -> None:
        self._ttl = (
            ttl_seconds if ttl_seconds is not None else settings.session_ttl_seconds
        )
        self._sessions: dict[str, Session] = {}

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items() if now - s.last_access > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]

    def get_or_create(
        self, session_id: str | None, airport_id: str | None = None
    ) -> Session:
        self._evict_expired()
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.touch()
            if airport_id:
                session.airport_id = airport_id
            return session

        new_id = session_id or uuid.uuid4().hex
        session = Session(
            session_id=new_id,
            airport_id=airport_id or settings.default_airport_id,
        )
        self._sessions[new_id] = session
        return session

    def __len__(self) -> int:  # handy for tests
        return len(self._sessions)


# Process-wide store (single-worker dev default).
store = SessionStore()
