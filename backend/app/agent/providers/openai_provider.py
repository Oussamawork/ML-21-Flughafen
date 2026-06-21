"""OpenAI tool-calling provider (selected by LLM_PROVIDER=openai).

The `openai` SDK is imported lazily so the package stays importable with no SDK and
no key under the default offline provider. Untested without a key — wire OPENAI_API_KEY
to exercise it.
"""

from __future__ import annotations

import json

from ..prompts import system_prompt
from .base import LLMResult, ToolCallReq, ToolSpec


class OpenAIProvider:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY required for LLM_PROVIDER=openai")
        from openai import OpenAI  # lazy

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def _to_openai_messages(
        self,
        messages: list[dict],
        airport_id: str,
        language: str,
        flight_number: str | None,
        position: str | None,
    ) -> list[dict]:
        out = [{"role": "system", "content": system_prompt(airport_id, language)}]
        # Tell the model the passenger's TYPED context so it calls tools with the
        # real flight number instead of the schema's example code.
        ctx = []
        if flight_number:
            ctx.append(
                f"the passenger's flight number is {flight_number} — use exactly this "
                f"for flight/gate tools; never substitute an example code"
            )
        if position:
            ctx.append(f"the passenger is currently at node '{position}'")
        if ctx:
            out.append({"role": "system", "content": "Passenger context: " + "; ".join(ctx) + "."})
        for m in messages:
            role = m.get("role")
            if role == "tool":
                out.append({
                    "role": "tool",
                    "tool_call_id": m.get("tool_call_id"),
                    "content": json.dumps(m.get("result")),
                })
            elif role == "assistant" and m.get("tool_calls"):
                out.append({
                    "role": "assistant",
                    "content": m.get("content") or None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])},
                        }
                        for tc in m["tool_calls"]
                    ],
                })
            else:
                out.append({"role": role, "content": m.get("content", "")})
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
            {"type": "function", "function": {"name": t.name, "parameters": t.json_schema}}
            for t in tools
        ]
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=self._to_openai_messages(messages, airport_id, language, flight_number, position),
            tools=tool_defs or None,
            temperature=0,  # faithful to tool results; reduce hallucination
        )
        choice = resp.choices[0].message
        if choice.tool_calls:
            calls = [
                ToolCallReq(
                    tc.function.name,
                    json.loads(tc.function.arguments or "{}"),
                    id=tc.id,
                )
                for tc in choice.tool_calls
            ]
            return LLMResult(tool_calls=calls, intent="find_gate")
        return LLMResult(content=choice.content, intent="smalltalk")
