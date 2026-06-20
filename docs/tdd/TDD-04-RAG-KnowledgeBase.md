# TDD-04 — Airport Knowledge Base & RAG

**Component:** `knowledge_base/`
**Status:** ⚪ Not started
**Depends on:** none · **Consumed by:** TDD-03 (services/directions/faq), TDD-02

---

## 1. Purpose

A modular, **airport-agnostic** knowledge base, queried through
Retrieval-Augmented Generation, that supplies grounded facts about an airport:
services, layout/zones, directions, and FAQ. Demonstrated on AUH; a new airport
is added by dropping in a data pack — no code changes.

## 2. Requirements satisfied

- *Modular, airport-agnostic knowledge base queryable through RAG.*
- *Construction of a reusable airport knowledge base, demonstrated on AUH.*

## 3. Design

### 3.1 Data model
Airport data lives under `knowledge_base/data/<airport_id>/`:
```
data/AUH/
├── airport.yaml        # metadata: name, terminals, timezone, languages
├── services.yaml       # list of services (type, name, zone, level, hours)
├── layout.yaml         # zones, connections (graph) for directions
└── faq/                # markdown docs: baggage.md, checkin.md, transit.md, ...
```
Each record carries `airport_id` so collections can be multi-airport or per-airport.

### 3.2 Ingestion pipeline
```
yaml/markdown ─▶ chunk (semantic, ~300 tokens) ─▶ embed ─▶ ChromaDB collection
                                                   (metadata: airport_id, type, source)
```
- **Embeddings:** multilingual model so Arabic/Darija/French queries match
  Arabic/French content (e.g. `intfloat/multilingual-e5-base` or
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`). Config-selected.
- **Store:** ChromaDB (persistent local dir). One collection `airport_kb`,
  filtered by `airport_id` metadata at query time.

### 3.3 Retrieval
```python
def retrieve(query: str, airport_id: str, k: int = 5,
             type_filter: str | None = None) -> list[Chunk]
```
- Embeds the query, filters by `airport_id` (+ optional `type` e.g. `service`,
  `faq`, `layout`), returns top-k chunks with source ids.
- Returned chunks are passed to the agent/tool which composes a grounded answer
  and cites `sources`.

### 3.4 Airport-agnostic guarantee
- No airport names/zones in code; everything from the data pack.
- Adding "CMN" = create `data/CMN/`, run `ingest.py --airport CMN`, set
  `AIRPORT_ID=CMN`. Verified by an ingestion test on a second tiny fixture.

## 4. Interfaces & data contracts

```python
class KnowledgeBase:
    def ingest(self, airport_id: str) -> int            # returns #chunks
    def retrieve(self, query, airport_id, k=5, type_filter=None) -> list[Chunk]

# Chunk
{ "text": "...", "type": "service|faq|layout|airport",
  "airport_id": "AUH", "source": "kb://AUH/services#pharmacy-T1", "score": 0.82 }
```
Consumed by `find_service`, `directions`, `faq` tools (TDD-03).

## 5. Dependencies

`chromadb`, `sentence-transformers` (or e5 via `transformers`), `PyYAML`,
`markdown`/`tiktoken` for chunking. Env: `KB_EMBEDDING_MODEL`, `KB_PERSIST_DIR`.

## 6. Open questions / risks

- **Multilingual retrieval quality** for Darija queries → pick a strong
  multilingual embedder; optionally translate query to MSA before embed.
- **AUH data sourcing** — assemble services/layout/FAQ from public info; mark
  approximations clearly (it's a case-study demo, not an official dataset).
- **`directions` as graph vs RAG** — layout is better as a small graph (BFS)
  than pure RAG; KB stores the graph, `directions` runs pathfinding.

## 7. Task checklist

- [ ] Define YAML schemas (airport/services/layout) + FAQ markdown
- [ ] Author AUH data pack (case study)
- [ ] `ingest.py` (chunk + embed + ChromaDB) with `airport_id` metadata
- [ ] `retrieve()` with airport/type filters
- [ ] `directions` pathfinding over layout graph
- [ ] Second-airport fixture test (agnostic guarantee)
