# TDD-02 — LLM Agent (Agentic Orchestration)

**Component:** `agent/`
**Status:** ⚪ Not started
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
  ReAct loop because the tool trace is needed for evaluation/debugging).
- **LLM:** GPT-4o-mini (default) via API, with a config switch to Llama 3.1 via
  Groq. Selected by env var `LLM_PROVIDER`.

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
              language: str | None = None) -> AgentResult
```
```jsonc
// AgentResult
{
  "answer": "Your gate is B12, Terminal 1. Boarding at 14:35.",
  "language": "en",
  "intent": "find_gate",
  "tool_trace": [
    {"tool": "flight_status", "args": {"flight": "SV-624"},
     "result": {"gate": "B12", "terminal": "T1", "boarding": "14:35"}}
  ]
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
  weaker. Mitigate with examples; consider the fine-tuned intent classifier.
- **Tool-loop cost/latency** — cap hops; cache flight lookups per session.
- **Language consistency** — enforce reply-language in `compose_answer` + a guard.

## 7. Task checklist

- [ ] Scaffold `agent/` package + config (LLM provider switch)
- [ ] Implement LangGraph graph + state
- [ ] System prompt + few-shot (incl. Darija)
- [ ] Wire tools (TDD-03) and RAG (TDD-04)
- [ ] `run_agent` interface + unit tests with mocked tools
- [ ] (stretch) fine-tuned intent classifier
