"""ChromaDB + multilingual-embedding retriever (TDD-04) — the default RAG backend.

Runs entirely locally on CPU (no API key): the embedding model (KB_EMBEDDING_MODEL,
default multilingual e5) is loaded lazily so importing this module is cheap and the
test suite (which uses the keyword backend) never pulls it in. The persistent store
lives at KB_PERSIST_DIR; build it with `python -m app.kb.ingest`.
"""

from __future__ import annotations

from ...config import settings
from .base import Chunk

COLLECTION = "airport_kb"

_model = None  # cached SentenceTransformer (load once)


def _embedder():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.kb_embedding_model, device="cpu")
    return _model


def _is_e5() -> bool:
    # e5 models expect "query:"/"passage:" prefixes for best retrieval quality.
    return "e5" in settings.kb_embedding_model.lower()


def embed_queries(texts: list[str]) -> list[list[float]]:
    pre = [f"query: {t}" for t in texts] if _is_e5() else texts
    return _embedder().encode(pre, normalize_embeddings=True).tolist()


def embed_documents(texts: list[str]) -> list[list[float]]:
    pre = [f"passage: {t}" for t in texts] if _is_e5() else texts
    return _embedder().encode(pre, normalize_embeddings=True).tolist()


def get_collection():
    import chromadb

    client = chromadb.PersistentClient(path=settings.kb_persist_dir)
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def _where(airport_id: str, type_filter: str | None) -> dict:
    clauses = [{"airport_id": airport_id.upper()}]
    if type_filter:
        clauses.append({"type": type_filter})
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


class ChromaRetriever:
    def __init__(self) -> None:
        self._col = None

    def _collection(self):
        if self._col is None:
            self._col = get_collection()
        return self._col

    def retrieve(
        self,
        query: str,
        airport_id: str,
        k: int = 3,
        type_filter: str | None = None,
        lang: str | None = None,
    ) -> list[Chunk]:
        col = self._collection()
        if col.count() == 0:  # not ingested yet -> degrade gracefully
            return []
        res = col.query(
            query_embeddings=embed_queries([query]),
            n_results=max(k * 3, 6),
            where=_where(airport_id, type_filter),
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        seen_topics: set[str] = set()
        out: list[Chunk] = []
        for doc, meta, dist in zip(docs, metas, dists):
            topic = meta.get("topic")
            if topic in seen_topics:
                continue
            seen_topics.add(topic)
            chosen = self._localize(col, airport_id, topic, lang) or (doc, meta)
            text, cmeta = chosen
            out.append(
                Chunk(
                    text=text,
                    type=cmeta.get("type", "faq"),
                    airport_id=cmeta.get("airport_id", airport_id.upper()),
                    source=cmeta.get("source", ""),
                    lang=cmeta.get("lang", ""),
                    score=round(1.0 - float(dist), 3),
                )
            )
            if len(out) >= k:
                break
        return out

    def _localize(self, col, airport_id: str, topic: str, lang: str | None):
        """Fetch the requested-language variant of `topic` so the answer matches
        the user's language even if another language scored highest."""
        if not lang or not topic:
            return None
        got = col.get(
            where={"$and": [{"airport_id": airport_id.upper()}, {"topic": topic}, {"lang": lang}]}
        )
        docs, metas = got.get("documents", []), got.get("metadatas", [])
        if docs:
            return docs[0], metas[0]
        return None
