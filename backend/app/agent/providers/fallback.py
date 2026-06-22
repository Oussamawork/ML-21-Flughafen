"""Ordered LLM fallback chain. Tries each provider in turn and returns the first
success; raises only if all fail. Used so a hosted primary (e.g. Anthropic)
degrades to Groq, then to the deterministic offline brain — the turn never crashes.
"""

from __future__ import annotations

import logging

from .base import LLMResult, LLMProvider

logger = logging.getLogger(__name__)


class FallbackProvider:
    def __init__(self, providers: list[LLMProvider]) -> None:
        self._providers = list(providers)

    def complete(self, **kwargs) -> LLMResult:
        last_exc: Exception | None = None
        for provider in self._providers:
            try:
                return provider.complete(**kwargs)
            except Exception as exc:  # try the next provider in the chain
                logger.warning("LLM provider %s failed: %s", type(provider).__name__, exc)
                last_exc = exc
        if last_exc:
            raise last_exc
        raise RuntimeError("no fallback providers configured")
