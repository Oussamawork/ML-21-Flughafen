"""Dependency-free retriever (TDD-04). Token-overlap scoring over the pack's FAQ
chunks — no embeddings, no model download. Used by the test suite (KB_RETRIEVER=
keyword) and as the fallback when the embedding stack is unavailable. Cross-lingual
recall is weak (that's what the chroma backend is for), so it also matches across
all language variants of a topic to stay useful offline.
"""

from __future__ import annotations

import re

from ..loader import load_pack
from .base import Chunk, faq_chunks

_WORD = re.compile(r"\w+", re.UNICODE)

# Drop high-frequency stopwords so lexical overlap reflects content words, not
# shared "what/do/i" filler (ar/ary/fr/en). Keeps the offline retriever sensible.
_STOP = {
    "i", "me", "my", "you", "the", "a", "an", "is", "are", "do", "does", "did",
    "what", "where", "how", "when", "to", "for", "of", "in", "on", "at", "can",
    "should", "it", "this", "that", "and", "or", "with", "about", "there",
    "je", "le", "la", "les", "un", "une", "est", "où", "comment", "pour", "de",
    "des", "à", "ma", "mon", "quoi", "que", "ce", "se", "il",
    "في", "من", "على", "ما", "أين", "اين", "كيف", "هل", "إلى", "عن", "و", "هاد",
}


def _tokens(text: str) -> set[str]:
    return {t for t in (w.lower() for w in _WORD.findall(text)) if t not in _STOP}


class KeywordRetriever:
    def retrieve(
        self,
        query: str,
        airport_id: str,
        k: int = 3,
        type_filter: str | None = None,
        lang: str | None = None,
    ) -> list[Chunk]:
        if type_filter not in (None, "faq"):
            return []
        pack = load_pack(airport_id)
        records = faq_chunks(pack)
        q = _tokens(query)
        if not q:
            return []
        # Score every (topic, lang) chunk; keep the best chunk per topic, then
        # return that topic's answer in the requested language when available.
        best_by_topic: dict[str, tuple[float, dict]] = {}
        for rec in records:
            overlap = len(q & _tokens(rec["embed_text"]))
            if not overlap:
                continue
            score = overlap / (len(q) or 1)
            cur = best_by_topic.get(rec["topic"])
            if cur is None or score > cur[0]:
                best_by_topic[rec["topic"]] = (score, rec)

        ranked = sorted(best_by_topic.values(), key=lambda x: x[0], reverse=True)[:k]
        out: list[Chunk] = []
        for score, rec in ranked:
            chosen = _localize(records, rec["topic"], lang) or rec
            out.append(
                Chunk(
                    text=chosen["text"],
                    type="faq",
                    airport_id=pack.airport_id,
                    source=chosen["source"],
                    lang=chosen["lang"],
                    score=round(score, 3),
                )
            )
        return out


def _localize(records: list[dict], topic: str, lang: str | None) -> dict | None:
    if not lang:
        return None
    for rec in records:
        if rec["topic"] == topic and rec["lang"] == lang:
            return rec
    return None
