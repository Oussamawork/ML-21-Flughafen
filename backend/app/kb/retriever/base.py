"""Retriever interface (TDD-04 §3.3) — the one seam the `faq` RAG tool depends on.

Two backends implement it (selected by KB_RETRIEVER): `chroma` (real multilingual
embeddings, the default for running the app) and `keyword` (dependency-free token
overlap, used by the test suite so pytest never downloads a model). Mirrors the LLM
provider pattern (agent/providers/).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..loader import Pack


@dataclass
class Chunk:
    text: str          # the answer text returned to the user
    type: str          # "faq" | "service" | ...
    airport_id: str
    source: str        # e.g. kb://AUH/faq/baggage#ary
    lang: str
    score: float = 0.0


def faq_chunks(pack: Pack) -> list[dict]:
    """Flatten the pack's FAQ into one (topic, lang) record each. Shared by both
    retrievers and the ingester so the corpus is defined in exactly one place.

    `embed_text` is what gets embedded/matched (question + answer for recall);
    `text` is the answer alone (what we return)."""
    records: list[dict] = []
    for entry in pack.faq:
        topic = entry.get("topic") or entry.get("id")
        for lang, variant in (entry.get("variants") or {}).items():
            question = (variant or {}).get("question", "")
            answer = (variant or {}).get("answer", "")
            if not answer:
                continue
            records.append(
                {
                    "id": f"{pack.airport_id}:faq:{topic}:{lang}",
                    "topic": topic,
                    "lang": lang,
                    "text": answer,
                    "embed_text": f"{question} {answer}".strip(),
                    "source": f"kb://{pack.airport_id}/faq/{topic}#{lang}",
                }
            )
    return records


class Retriever(Protocol):
    def retrieve(
        self,
        query: str,
        airport_id: str,
        k: int = 3,
        type_filter: str | None = None,
        lang: str | None = None,
    ) -> list[Chunk]: ...
