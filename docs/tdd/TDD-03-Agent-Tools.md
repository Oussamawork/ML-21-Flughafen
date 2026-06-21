# TDD-03 — Agent Tools & Flight Data Integration

**Component:** `agent/tools/` (flight provider lives in `backend/app/services/flight.py` for now)
**Status:** 🟡 In progress — AirLabs flight provider + `/flight` built & live-verified; KB tools pending
**Depends on:** TDD-04 (KB for FAQ/services/layout/check-in), **AirLabs API** (flight data)
**Consumed by:** TDD-02 (agent), TDD-06 (`/flight` endpoint)

---

## 1. Purpose

Define the typed tools the agent can call, their schemas, and the integration with
a live flight-data API. Tools are pure-ish functions: typed args in, typed JSON
out, no LLM inside.

## 2. Requirements satisfied

- *Integrate a real-time flight data API (status, gate assignments, delays).*
- *Implement agent tools (flight status, gate finder, services, FAQ).*

## 3. Tool catalogue

| Tool | Purpose | Backed by |
|---|---|---|
| `flight_status` | Live status/gate/terminal/baggage/times for a flight number | **AirLabs** (§4) |
| `find_gate` | Gate + terminal for a flight (subset of status) | **AirLabs** (§4) |
| `find_service` | Nearby services (restroom, pharmacy, lounge, food) | KB / RAG (TDD-04) |
| `directions` | Route between two nodes (+ map polyline & walk time) | KB layout graph (TDD-04) |
| `faq` | General airport FAQ (baggage, check-in, transit) | RAG (TDD-04) |

> Notes: **baggage** is arrival-only (AirLabs `arr_baggage`); **check-in** is not in
> AirLabs → served from the KB. `directions` returns the route **as map nodes +
> positions** so the frontend can draw the airport-map polyline (TDD-07).

### 3.1 Schemas (JSON-schema-style, used for LLM tool-calling)

```jsonc
flight_status: {
  "args": { "flight_number": "string (IATA, e.g. SV624)", "airport_id": "AUH" },
  "returns": {
    "flight_number": "SV624", "airline": "SV", "status": "scheduled|active|landed|cancelled",
    "direction": "departure|arrival",        // which side matches airport_id
    "scheduled": "ISO8601", "estimated": "ISO8601|null", "actual": "ISO8601|null",
    "gate": "B12|null", "terminal": "A|null", "baggage": "10|null (arrivals only)",
    "delay_minutes": 0, "departure_airport": "AUH", "arrival_airport": "string",
    "aircraft": "A320|null", "source": "airlabs"
  }
}

directions: {
  "args": { "from_node": "entrance|<position>", "to_node": "gate-b12",
            "airport_id": "AUH" },
  "returns": {
    "steps": ["Head to ...", "..."],
    "route": ["entrance", "check-in", "security", "duty-free", "gate-b12"],
    "positions": { "entrance": {"x": 8, "y": 54}, "...": {} },   // for the map
    "route_summary": { "distance_m": 525, "walking_time_min": 7 }
  }
}

find_service: {
  "args": { "service_type": "pharmacy|restroom|lounge|food|atm|...",
            "near_zone": "string|null", "airport_id": "AUH" },
  "returns": { "results": [ { "name": "...", "zone": "Terminal 1, Gate B",
               "level": "Departures", "open_hours": "...", "distance_hint": "..." } ] }
}

faq: {
  "args": { "question": "string", "airport_id": "AUH" },
  "returns": { "answer": "string", "sources": ["kb://AUH/faq/baggage"] }
}
```

## 4. Flight data integration — AirLabs (v9)

**Provider: AirLabs** (`https://airlabs.co/api/v9`), chosen via
`FLIGHT_API_PROVIDER=airlabs`. Kept behind a `FlightProvider` adapter so a vendor
swap never touches the tools. **Verified live on a free key (2026-06-21).**

- **Interface:**
  ```python
  class FlightProvider(Protocol):
      def get_flight(self, flight_number: str) -> FlightStatus | None: ...
  ```
- **Primary call:** `GET /flight?flight_iata={code}&api_key=…` — single-flight
  lookup by the **typed** flight number (TDD-00 "identity over inference"). Returns
  `dep_terminal`, `dep_gate`, `arr_terminal`, `arr_gate`, `arr_baggage`, `status`,
  scheduled/estimated/actual times, `dep_delayed`/`arr_delayed`, airline, aircraft.
- **Board call (secondary):** `GET /schedules?dep_iata=AUH` / `arr_iata=AUH` for
  "departures/arrivals at AUH" queries and for `*_actual` times. `GET /airlines`,
  `GET /airports` enrich/validate codes (static — cache for days).
- **Airport scoping in code:** `/flight` has **no** airport filter, so after the
  lookup we compare `dep_iata`/`arr_iata` against `airport_id` (default `AUH`) to
  pick the departure vs arrival view, or report "this flight doesn't touch AUH".
- **Caching (mandatory):** free tier is only **1,000 req/month** (250/min,
  2,500/hr). Cache `/flight` & `/schedules` for `FLIGHT_CACHE_TTL` (default 60 s)
  keyed by flight number / airport+direction; cache static DBs for days.
- **Security:** the AirLabs response **echoes the `api_key`** in `response.request.key`
  — the backend MUST strip the `request`/meta block before returning to the FE. The
  key lives server-side only (`AIRLABS_API_KEY`), never in the frontend.
- **Coverage / nulls:** on live AUH departures `dep_terminal` ~98%, `dep_gate` ~89%,
  `status` 100%; `arr_baggage` is **arrival-only** (~35%). Missing fields → `null`;
  the card/map degrade gracefully (route to terminal when gate is unknown).
- **No check-in field:** AirLabs has none → check-in zone comes from the KB
  (TDD-04), keyed by `airport_id`.
- **Errors:** network/quota (`minute_limit_exceeded` / `hour_…` / `month_…`) raise
  `ToolUnavailable`; the agent degrades gracefully (TDD-00 §6).

## 5. Interfaces & data contracts

- Each tool is registered with the agent as `(name, json_schema, callable)`.
- Tools return plain dicts (JSON-serializable); no exceptions across the boundary
  except the typed `ToolUnavailable` / `ToolBadInput`.
- `airport_id` defaults from session/config; tools never hard-code AUH.

## 6. Dependencies

`httpx`/`requests` (API calls), `pydantic` (arg/result validation), KB client
(TDD-04). Env: `FLIGHT_API_PROVIDER=airlabs`, `AIRLABS_API_KEY` (server-side only),
`FLIGHT_CACHE_TTL` (default 60 s).

## 7. Open questions / risks

- **1,000 req/month free cap** → aggressive caching; consider a paid tier for the
  live demo, or pre-warm a cache of the case-study flights.
- Flight-number normalization (strip spaces/dashes, uppercase → `flight_iata`).
- Mock provider for offline dev/tests (the suite must never call AirLabs).
- Gate/baggage `null` for some flights → route to terminal; never fail the turn.

## 8. Task checklist

- [x] `FlightProvider` interface + **AirLabs** adapter + mock provider
      (`backend/app/services/flight.py`; default `mock` so it runs offline)
- [x] Normalization to canonical schema (+ airport scoping by `airport_id`) + tests
- [x] Strip AirLabs `request`/meta (key echo); send a `User-Agent` (AirLabs 403s
      the default urllib UA — found via live test)
- [x] Caching (TTL) + graceful `FlightUnavailable` on quota/network errors
- [x] `POST /flight` endpoint (TDD-06) consuming the provider; **live-verified**
- [ ] `flight_status` / `find_gate` exposed as **agent tools** (with TDD-02)
- [ ] `find_service` / `directions` (route + positions + summary) / `faq` over KB
- [ ] Tool registry + JSON schemas for the agent (TDD-02)
