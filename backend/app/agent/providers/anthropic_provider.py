"""Anthropic (Claude) tool-calling provider (selected by LLM_PROVIDER=anthropic).

The `anthropic` SDK is imported lazily so the package stays importable with no SDK
and no key under the default offline provider. Claude's tool API uses content
blocks (`tool_use` / `tool_result`) rather than the OpenAI-compatible
chat-completions shape, so this is its own adapter. Strong at instruction-following
and multilingual (Darija) output + tool discipline.
"""

from __future__ import annotations

import json

from ..prompts import system_prompt
from .base import LLMResult, ToolCallReq, ToolSpec


class AnthropicProvider:
    def __init__(self, api_key: str, model: str, max_tokens: int = 1024) -> None:
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY required for LLM_PROVIDER=anthropic")
        from anthropic import Anthropic  # lazy

        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def _system(self, airport_id, language, flight_number, position) -> str:
        text = system_prompt(airport_id, language)
        ctx = []
        if flight_number:
            ctx.append(
                f"the passenger's flight number is {flight_number} — use exactly this "
                f"for flight/gate tools; never substitute an example code"
            )
        if position:
            ctx.append(f"the passenger is currently at node '{position}'")
        if ctx:
            text += " Passenger context: " + "; ".join(ctx) + "."
        return text

    def _to_messages(self, messages: list[dict]) -> list[dict]:
        """Map our internal messages to Claude's blocks. Consecutive tool results
        are merged into one user message so user/assistant turns stay alternating."""
        out: list[dict] = []
        pending: list[dict] = []  # tool_result blocks awaiting a flush

        def flush() -> None:
            if pending:
                out.append({"role": "user", "content": list(pending)})
                pending.clear()

        for m in messages:
            role = m.get("role")
            if role == "tool":
                pending.append({
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id"),
                    "content": json.dumps(m.get("result")),
                })
                continue
            flush()
            if role == "assistant" and m.get("tool_calls"):
                content: list[dict] = []
                if m.get("content"):
                    content.append({"type": "text", "text": m["content"]})
                for tc in m["tool_calls"]:
                    content.append({
                        "type": "tool_use", "id": tc["id"],
                        "name": tc["name"], "input": tc["args"],
                    })
                out.append({"role": "assistant", "content": content})
            else:
                out.append({"role": role, "content": m.get("content", "")})
        flush()
        return out

    def complete(
        self,
        *,
        messages: list[dict],
        tools: list[ToolSpec],
        language: str,
        airport_id: str,
        flight_number: str | None,
        position: str | None = None,
    ) -> LLMResult:
        tool_defs = [
            {"name": t.name, "description": "", "input_schema": t.json_schema}
            for t in tools
        ]
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=0,  # faithful to tool results; reduce hallucination
            system=self._system(airport_id, language, flight_number, position),
            messages=self._to_messages(messages),
            tools=tool_defs or None,
        )
        calls = [
            ToolCallReq(b.name, dict(b.input), id=b.id)
            for b in resp.content if b.type == "tool_use"
        ]
        if calls:
            return LLMResult(tool_calls=calls, intent="find_gate")
        text = "".join(b.text for b in resp.content if b.type == "text")
        return LLMResult(content=text, intent="smalltalk")
