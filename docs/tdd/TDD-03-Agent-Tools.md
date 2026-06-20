# TDD-03 — Agent Tools & Flight Data Integration

**Component:** `agent/tools/`
**Status:** ⚪ Not started
**Depends on:** TDD-04 (RAG for FAQ/services), external Flight API
**Consumed by:** TDD-02 (agent)

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
| `flight_status` | Live status/gate/terminal/boarding for a flight number | Flight API |
| `find_gate` | Gate + terminal for a flight (subset of status) | Flight API |
| `find_service` | Nearby services (restroom, pharmacy, lounge, food) | KB / RAG (TDD-04) |
| `directions` | Step-by-step navigation between two points/zones | KB layout (TDD-04) |
| `faq` | General airport FAQ (baggage, check-in, transit) | RAG (TDD-04) |

### 3.1 Schemas (JSON-schema-style, used for LLM tool-calling)

```jsonc
flight_status: {
  "args": { "flight_number": "string (IATA/ICAO, e.g. SV624)" },
  "returns": {
    "flight_number": "SV624", "status": "scheduled|active|landed|cancelled|delayed",
    "scheduled_departure": "ISO8601", "estimated_departure": "ISO8601|null",
    "gate": "B12|null", "terminal": "T1|null", "delay_minutes": 0,
    "departure_airport": "AUH", "arrival_airport": "string", "source": "aviationstack"
  }
}

find_service: {
  "args": { "service_type": "pharmacy|restroom|lounge|food|atm|...",
            "near_zone": "string|null", "airport_id": "AUH" },
  "returns": { "results": [ { "name": "...", "zone": "Terminal 1, Gate B",
               "level": "Departures", "open_hours": "...", "distance_hint": "..." } ] }
}

directions: {
  "args": { "from_zone": "string", "to_zone": "string", "airport_id": "AUH" },
  "returns": { "steps": ["Head to ...", "Take elevator to ...", "..."],
               "est_walk_minutes": 6 }
}

faq: {
  "args": { "question": "string", "airport_id": "AUH" },
  "returns": { "answer": "string", "sources": ["kb://AUH/faq/baggage"] }
}
```

## 4. Flight data integration

- **Provider:** AviationStack (default) or AeroDataBox; chosen via
  `FLIGHT_API_PROVIDER`. Adapter pattern → one `FlightProvider` interface, one
  implementation per vendor, so we can swap without touching tools.
- **Interface:**
  ```python
  class FlightProvider(Protocol):
      def get_flight(self, flight_number: str) -> FlightStatus | None: ...
  ```
- **Caching:** per-flight result cached `FLIGHT_CACHE_TTL` (default 120 s) to
  respect free-tier rate limits.
- **Normalization:** vendor responses mapped to the canonical `flight_status`
  return schema above. Missing gate/terminal → `null` (common on free tiers).
- **Errors:** network/quota errors raise `ToolUnavailable`; the agent degrades
  gracefully (TDD-00 §6) and tells the user data is temporarily unavailable.

> ⚠️ Verify the chosen provider actually returns **gate/terminal** for AUH on the
> free tier; many only return status. If gates are unavailable live, the demo can
> fall back to KB-seeded gate data for the case-study flights.

## 5. Interfaces & data contracts

- Each tool is registered with the agent as `(name, json_schema, callable)`.
- Tools return plain dicts (JSON-serializable); no exceptions across the boundary
  except the typed `ToolUnavailable` / `ToolBadInput`.
- `airport_id` defaults from session/config; tools never hard-code AUH.

## 6. Dependencies

`httpx`/`requests` (API calls), `pydantic` (arg/result validation), KB client
(TDD-04). Env: `FLIGHT_API_PROVIDER`, `FLIGHT_API_KEY`, `FLIGHT_CACHE_TTL`.

## 7. Open questions / risks

- Free-tier **gate coverage** at AUH (see §4 warning).
- Flight-number normalization (IATA `SV624` vs ICAO `SVA624`, spaces/dashes).
- Rate limits → caching + a mock provider for offline dev/tests.

## 8. Task checklist

- [ ] `FlightProvider` interface + AviationStack adapter + mock provider
- [ ] Normalization to canonical schema + tests
- [ ] `flight_status` / `find_gate` tools
- [ ] `find_service` / `directions` / `faq` tools over KB (after TDD-04)
- [ ] Tool registry + JSON schemas for the agent
- [ ] Caching + graceful-degradation errors
