"""LLM provider selection (LLM_PROVIDER). Default = offline (no key)."""

from __future__ import annotations

from ...config import settings
from .base import LLMProvider, LLMResult, ToolCallReq, ToolSpec
from .fallback import FallbackProvider
from .offline import OfflineProvider

__all__ = [
    "LLMProvider",
    "LLMResult",
    "ToolCallReq",
    "ToolSpec",
    "OfflineProvider",
    "FallbackProvider",
    "build_llm_provider",
]


def build_llm_provider(name: str | None = None) -> LLMProvider:
    """Build a provider by name (defaults to LLM_PROVIDER). `name` lets the agent
    construct the Groq fallback explicitly even when Groq isn't the primary."""
    provider = name or settings.llm_provider
    if provider == "anthropic":
        from .anthropic_provider import AnthropicProvider  # lazy: needs the SDK

        return AnthropicProvider(settings.anthropic_api_key, settings.llm_model)
    if provider == "openai":
        from .openai_provider import OpenAIProvider  # lazy: needs the SDK

        return OpenAIProvider(settings.openai_api_key, settings.llm_model)
    if provider == "groq":
        from .groq_provider import GroqProvider  # lazy: needs the SDK

        # llm_model is the *primary's* model (maybe a Claude id) — when Groq is the
        # fallback, use the Groq-specific model instead.
        model = settings.llm_model if settings.llm_provider == "groq" else settings.groq_fallback_model
        return GroqProvider(settings.groq_api_key, model)
    return OfflineProvider()
