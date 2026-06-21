# TDD-02 — LLM Agent (Agentic Orchestration)

**Component:** `backend/app/agent/`
**Status:** 🟢 Built — LangGraph graph + LLM-provider interface (offline default,
Groq/OpenAI verified when keyed) + full tool set wired & default-on (flight tools
TDD-03 + KB `directions`/`find_service`/`faq` TDD-04)
**Depends on:** TDD-03 (tools), TDD-04 (RAG) · **Consumed by:** TDD-06 (`/chat`)

---

## 1. Purpose

The reasoning core. Given the passenger's text (from STT or typed) it: detects
the language, infers intent, decides which tool(s) to call, grounds the answer in
tool/RAG results, and produces a contextual reply **in the passenger's language**.

## 2. Requirements satisfied

- *General-purpose agentic architecture based on an LLM with tool-calling.*
- *Identify the passenger's intent; respond contextually and personally.*
- *Multilingual interaction (Arabic/Darija/French/English).*

## 3. Design

### 3.1 Framework
- **LangGraph** for an explicit, inspectable state graph (preferred over a plain
  ReAct loop because the tool trace is needed for evaluation/debugging). Lives in
  `backend/app/agent/` (subpackage under `app.` — the documented `agent/` dir name;
  kept in-package so the backend imports it cleanly).
- **LLM behind a provider interface** (`LLMProvider.complete`), selected by
  `LLM_PROVIDER`: **`offline` (default)** is deterministic and **needs no API key**
  (keeps the pipeline runnable offline); `openai` (GPT-4o-mini) and `groq`
  (Llama 3.1) are lazy-imported and used once a key is wired. The model is a config
  choice made later — the graph/tools are model-agnostic.
- Enabled by default: `AGENT_BACKEND=langgraph` (fallback `stub`).

### 3.2 Graph
```
        ┌──────────────┐
input ─▶│ detect_lang  │
        └──────┬───────┘
        ┌──────▼───────┐    needs tool?
        │   agent_llm  │───────────────┐
        └──────┬───────┘               │ yes
            no │ (direct answer)   ┌────▼─────┐
               │                   │  tools   │ (flight/gate/services/faq)
               │                   └────┬─────┘
               │              results   │
               │              ┌─────────▼────────┐
               └─────────────▶│   compose_answer │──▶ output
                              └──────────────────┘
```
- `detect_lang`: fast language ID → sets `state.language`.
- `agent_llm`: tool-calling model; emits either a final answer or tool calls.
- `tools`: executes the requested tool(s) (TDD-03), appends results to state.
- Loop `agent_llm → tools` up to `MAX_TOOL_HOPS` (default 4) to prevent runaway.
- `compose_answer`: final natural-language reply in `state.language`.

### 3.3 State
```python
class AgentState(TypedDict):
    session_id: str
    airport_id: str          # default "AUH"
    flight_number: str | None  # typed by the user (NOT parsed from STT) — TDD-00
    position: str | None       # user's current node in the airport map (TDD-04)
    language: str            # ar | ary | fr | en
    messages: list[Message]  # running conversation
    tool_trace: list[ToolCall]
    answer: str | None
```

### 3.4 Intent set (v1)
`flight_status`, `find_gate`, `find_terminal`, `find_service`, `directions`,
`faq_general`, `smalltalk/other`. Intent is handled implicitly by the LLM's tool
choice; an explicit fine-tuned intent classifier is a **stretch goal** (would add
a second owned model — see TDD-08 metrics).

### 3.5 Prompting
- System prompt encodes: role (airport assistant), airport_id, the rule "reply in
  the user's language", tool-use policy, and refusal/uncertainty behavior.
- Few-shot examples include a Darija example mirroring the proposal
  (*"ayna bawwabati, rihlati SV-624"*).

## 4. Interfaces & data contracts

```python
def run_agent(text: str, session_id: str, airport_id: str = "AUH",
              language: str | None = None, flight_number: str | None = None,
              position: str | None = None) -> AgentResult
```
```jsonc
// AgentResult — may carry structured flight/route payloads for the UI dashboard
{
  "answer": "Your gate is B12, Terminal A. Boarding from the South Pier.",
  "language": "en",
  "intent": "find_gate",
  "tool_trace": [
    {"tool": "flight_status", "args": {"flight_number": "SV624", "airport_id": "AUH"},
     "result": {"gate": "B12", "terminal": "A", "status": "scheduled", "source": "airlabs"}}
  ],
  "flight": { "flight_number": "SV624", "gate": "B12", "terminal": "A", "status": "scheduled" },
  "route":  { "route": ["entrance","check-in","security","duty-free","gate-b12"],
              "route_summary": { "distance_m": 525, "walking_time_min": 7 } }
}
```
- Tool schemas: TDD-03. Session/history storage: TDD-06.

## 5. Dependencies

`langgraph`, `langchain-core`, LLM SDK (`openai` and/or `groq`), a language-ID lib
(e.g. `fasttext`/`lingua`), plus tools (TDD-03) and RAG (TDD-04).

## 6. Open questions / risks

- **Hosted vs self-hosted LLM** — impacts cost/privacy and the "owned model"
  narrative; Whisper remains the primary owned model regardless.
- **Darija understanding by the LLM** — GPT-4o-mini handles Arabic well; Darija is
  weaker. Mitigate with examples; consider the fine-tuned intent classifier. Note:
  the **flight number is a typed field, not parsed from speech** (TDD-00 "identity
  over inference"), so flight lookups never depend on the LLM/STT reading a code.
- **Tool-loop cost/latency** — cap hops; cache flight lookups per session.
- **Language consistency** — enforce reply-language in `compose_answer` + a guard.

## 7. Task checklist

- [x] Scaffold `backend/app/agent/` package + config (`LLM_PROVIDER`/`LLM_MODEL`/`MAX_TOOL_HOPS`)
- [x] LangGraph graph + state (`detect_lang → agent_llm → tools* → compose`, hop cap)
- [x] LLM-provider interface: `OfflineProvider` (default, no key) + lazy `OpenAI`/`Groq`
- [x] System prompt + few-shot (incl. Darija) + multilingual answer templates
- [x] Wire flight tools (TDD-03 `flight_status`/`find_gate`); graceful `ToolUnavailable`
- [x] `Agent.run` integration (kept the backend Protocol) + 11 unit tests (mock tools, offline)
- [x] Default-on (`AGENT_BACKEND=langgraph`); existing API tests pass unchanged; live-verified
- [ ] Wire RAG/KB tools (`find_service`/`directions`/`faq`) with TDD-04
- [ ] Verify hosted LLM path (OpenAI/Groq) once a key is wired; pick the model
- [x] Thread typed `flight_number`/`position` from the dashboard → `/chat` & `/converse`
      → agent (ticket-strip number grounds answers without repeating the code)
- [ ] (stretch) fine-tuned intent classifier
