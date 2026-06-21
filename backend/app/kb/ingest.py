"""Ingest an airport data pack into ChromaDB (TDD-04 §3.2).

Chunks the pack's FAQ (one record per topic+language), embeds it with the
multilingual model, and upserts into the persistent `airport_kb` collection with
`airport_id`/`type`/`topic`/`lang` metadata so retrieval can filter per airport.

    cd backend && python -m app.kb.ingest --airport AUH
    python -m app.kb.ingest --all          # every pack under kb/data/
"""

from __future__ import annotations

import argparse

from .loader import available_airports, load_pack
from .retriever.base import faq_chunks


def ingest_airport(airport_id: str) -> int:
    """(Re)embed and store one airport's FAQ. Returns the #chunks written."""
    from .retriever.chroma import embed_documents, get_collection

    pack = load_pack(airport_id)
    records = faq_chunks(pack)
    if not records:
        return 0
    col = get_collection()
    # Idempotent: drop this airport's existing chunks before re-adding.
    col.delete(where={"airport_id": pack.airport_id})
    col.add(
        ids=[r["id"] for r in records],
        documents=[r["text"] for r in records],
        embeddings=embed_documents([r["embed_text"] for r in records]),
        metadatas=[
            {
                "airport_id": pack.airport_id,
                "type": "faq",
                "topic": r["topic"],
                "lang": r["lang"],
                "source": r["source"],
            }
            for r in records
        ],
    )
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest airport data packs into ChromaDB.")
    parser.add_argument("--airport", help="Airport id (e.g. AUH).")
    parser.add_argument("--all", action="store_true", help="Ingest every pack.")
    args = parser.parse_args()

    targets = available_airports() if args.all else [args.airport]
    if not targets or targets == [None]:
        parser.error("pass --airport <id> or --all")
    for aid in targets:
        n = ingest_airport(aid)
        print(f"ingested {aid}: {n} chunks")


if __name__ == "__main__":
    main()
