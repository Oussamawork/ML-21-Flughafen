"""Groq tool-calling provider (selected by LLM_PROVIDER=groq).

Groq's API is OpenAI-compatible for chat+tools; the `groq` SDK is imported lazily.
Untested without a key — wire GROQ_API_KEY to exercise it.
"""

from __future__ import annotations

import json

from ..prompts import SYSTEM_PROMPT
from .base import LLMResult, ToolCallReq, ToolSpec


class GroqProvider:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise RuntimeError("GROQ_API_KEY required for LLM_PROVIDER=groq")
        from groq import Groq  # lazy

        self._client = Groq(api_key=api_key)
        self._model = model

    def _to_messages(self, messages: list[dict], airport_id: str) -> list[dict]:
        out = [{"role": "system", "content": SYSTEM_PROMPT.format(airport_id=airport_id)}]
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
    ) -> LLMResult:
        tool_defs = [
            {"type": "function", "function": {"name": t.name, "parameters": t.json_schema}}
            for t in tools
        ]
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=self._to_messages(messages, airport_id),
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
