"""Retriever selection (TDD-04). KB_RETRIEVER picks the backend; mirrors
build_llm_provider() (agent/providers/). The heavy chroma/embedding imports stay
lazy inside the backend module so this import is cheap and key/GPU-free."""

from __future__ import annotations

from ...config import settings
from .base import Chunk, Retriever, faq_chunks

__all__ = ["Chunk", "Retriever", "faq_chunks", "build_retriever"]


def build_retriever(name: str | None = None) -> Retriever:
    name = (name or settings.kb_retriever).lower()
    if name == "keyword":
        from .keyword import KeywordRetriever

        return KeywordRetriever()
    if name == "chroma":
        from .chroma import ChromaRetriever

        return ChromaRetriever()
    raise ValueError(f"Unknown KB_RETRIEVER {name!r} (expected 'chroma' or 'keyword').")
