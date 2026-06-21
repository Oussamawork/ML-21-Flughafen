"""LangGraph state graph (TDD-02 §3.2):

  detect_lang -> agent_llm -> [tools -> agent_llm]* -> compose_answer -> END

The agent_llm node delegates to the LLMProvider (offline by default). The tools
node runs the requested tool and feeds the result back; the loop is capped at
MAX_TOOL_HOPS. Tool errors are caught here so a turn never crashes.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ..services.lang import detect_language
from .prompts import template
from .providers.base import LLMProvider, ToolSpec
from .state import AgentState
from .tools import Tool, ToolBadInput, ToolUnavailable


def _latest_user_text(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content") or ""
    return ""


def build_graph(provider: LLMProvider, registry: dict[str, Tool], max_hops: int):
    tool_specs = [ToolSpec(t.name, t.json_schema) for t in registry.values()]

    def detect_lang(state: AgentState) -> dict:
        if state.get("language"):
            return {}
        return {"language": detect_language(_latest_user_text(state["messages"]))}

    def agent_llm(state: AgentState) -> dict:
        result = provider.complete(
            messages=state["messages"],
            tools=tool_specs,
            language=state["language"],
            airport_id=state["airport_id"],
            flight_number=state.get("flight_number"),
        )
        if result.tool_calls:
            return {
                "pending_calls": [
                    {"tool": c.tool, "args": c.args} for c in result.tool_calls
                ],
                "intent": result.intent,
            }
        return {"answer": result.content, "intent": result.intent, "pending_calls": []}

    def tools(state: AgentState) -> dict:
        trace = list(state["tool_trace"])
        messages = list(state["messages"])
        for call in state["pending_calls"]:
            name, args = call["tool"], call["args"]
            tool = registry.get(name)
            if tool is None:
                result: dict | None = {"error": f"unknown tool {name}"}
            else:
                try:
                    result = tool.fn(**args)
                except (ToolUnavailable, ToolBadInput) as exc:
                    result = {"error": str(exc)}
            trace.append({"tool": name, "args": args, "result": result})
            messages.append({"role": "tool", "name": name, "result": result})
        return {
            "tool_trace": trace,
            "messages": messages,
            "pending_calls": [],
            "hops": state["hops"] + 1,
        }

    def compose_answer(state: AgentState) -> dict:
        if state.get("answer"):
            return {}
        return {"answer": template("fallback", state["language"]),
                "intent": state.get("intent") or "smalltalk"}

    def route_after_llm(state: AgentState) -> str:
        if state.get("pending_calls") and state["hops"] < max_hops:
            return "tools"
        return "compose"

    g = StateGraph(AgentState)
    g.add_node("detect_lang", detect_lang)
    g.add_node("agent_llm", agent_llm)
    g.add_node("tools", tools)
    g.add_node("compose", compose_answer)
    g.add_edge(START, "detect_lang")
    g.add_edge("detect_lang", "agent_llm")
    g.add_conditional_edges("agent_llm", route_after_llm, {"tools": "tools", "compose": "compose"})
    g.add_edge("tools", "agent_llm")
    g.add_edge("compose", END)
    return g.compile()
