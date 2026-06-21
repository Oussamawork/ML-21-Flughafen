# TDD-04 — Airport Knowledge Base & RAG

**Component:** `backend/app/kb/` (lives inside the backend package, like the agent
in `backend/app/agent/` — imported with the `app.` prefix, shares the service container)
**Status:** 🟢 Built — per-`airport_id` YAML data pack + map-graph directions +
service index + ChromaDB/multilingual-embedding FAQ RAG; exposed as the agent's
`directions`/`find_service`/`faq` tools and the `/map` endpoint. Live-verified.
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
├── checkin.yaml        # check-in zones/desks per airline/terminal (AirLabs has none)
├── layout.yaml         # map graph: nodes, positions (x,y %), edges w/ distances
└── faq/                # markdown docs: baggage.md, checkin.md, transit.md, ...
```
Each record carries `airport_id` so collections can be multi-airport or per-airport.

**`layout.yaml`** is the airport-map model that powers both `directions` (TDD-03)
and the frontend map (TDD-07). It holds:
```yaml
nodes:        { entrance: "Main entrance", "gate-b12": "Gate B12", ... }
positions:    { entrance: {x: 8, y: 54}, "gate-b12": {x: 78, y: 43}, ... }  # % coords
edges:        { security: [ {to: duty-free, distance_m: 85}, ... ], ... }
gate_nodes:   { B12: "gate-b12", ... }      # AirLabs gate code → graph node
baggage_nodes:{ "10": "baggage-10", ... }   # AirLabs arr_baggage → graph node
```
The **AUH layout is seeded from the teammate's SkyGuide `airport_map.json` +
edge-distance table** (reused as data, not code), then kept airport-agnostic under
`data/AUH/`. `checkin.yaml` fills the gap AirLabs leaves (no check-in field).

### 3.2 Ingestion pipeline
```
yaml/markdown ─▶ chunk (semantic, ~300 tokens) ─▶ embed ─▶ ChromaDB collection
                                                   (metadata: airport_id, type, source)
```
- **Embeddings:** multilingual model so Arabic/Darija/French queries match
  Arabic/French content. Default `intfloat/multilingual-e5-base` (`KB_EMBEDDING_MODEL`),
  CPU, loaded lazily. e5 query/passage prefixes applied automatically.
- **Store:** ChromaDB (persistent local dir `KB_PERSIST_DIR`). One collection
  `airport_kb`; each FAQ topic is stored as one chunk **per language**
  (metadata `airport_id`/`type`/`topic`/`lang`/`source`), so retrieval filters by
  `airport_id` and returns the answer in the user's language.
- **Retriever behind an interface** (`KB_RETRIEVER`, mirrors the LLM provider
  pattern): `chroma` (default — real embeddings, local, no key) and `keyword`
  (dependency-free token overlap) so the **test suite never downloads a model**.
  Build the store with `python -m app.kb.ingest --airport AUH` (or `--all`).

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
- **`directions` as graph vs RAG** — layout is better as a small graph (BFS/
  Dijkstra) than pure RAG; KB stores the graph (nodes/positions/edge distances),
  `directions` runs pathfinding and returns `route` + `positions` + `route_summary`
  ({distance_m, walking_time_min}) so the frontend can draw the map polyline.

## 7. Task checklist

- [x] Define YAML schemas (airport/services/checkin/layout/faq) — `backend/app/kb/data/AUH/`
- [x] `layout.yaml`: nodes + positions (x,y %) + edges w/ distances + gate/baggage
      node maps — **seeded AUH from SkyGuide `airport_map.json` + its edge table**
- [x] `checkin.yaml` for AUH (fills the AirLabs check-in gap)
- [x] Author rest of AUH data pack (services, FAQ in ar/ary/fr/en)
- [x] `ingest.py` (chunk + embed + ChromaDB) with `airport_id`/`type`/`lang` metadata
- [x] `retrieve()` with airport/type filters + language localization (chroma + keyword)
- [x] `directions` pathfinding → `route` + `steps` + `positions` + `route_summary`
- [x] `find_service` (structured filter) + `faq` (RAG) tools; `/map` endpoint + check-in
- [x] Second-airport fixture test (agnostic guarantee) — `tests/test_kb.py`
- Known limitation (§6): short **Darija** FAQ queries retrieve less reliably than
  ar/fr/en with e5-base; the owned Darija model is Whisper (TDD-01), RAG is infra.
