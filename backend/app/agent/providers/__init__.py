"""LLM provider selection (LLM_PROVIDER). Default = offline (no key)."""

from __future__ import annotations

from ...config import settings
from .base import LLMProvider, LLMResult, ToolCallReq, ToolSpec
from .offline import OfflineProvider

__all__ = [
    "LLMProvider",
    "LLMResult",
    "ToolCallReq",
    "ToolSpec",
    "OfflineProvider",
    "build_llm_provider",
]


def build_llm_provider() -> LLMProvider:
    provider = settings.llm_provider
    if provider == "openai":
        from .openai_provider import OpenAIProvider  # lazy: needs the SDK

        return OpenAIProvider(settings.openai_api_key, settings.llm_model)
    if provider == "groq":
        from .groq_provider import GroqProvider  # lazy: needs the SDK

        return GroqProvider(settings.groq_api_key, settings.llm_model)
    return OfflineProvider()
