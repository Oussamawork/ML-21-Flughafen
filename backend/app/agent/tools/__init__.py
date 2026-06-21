"""Agent tools (TDD-03). Typed args in, plain JSON dicts out, no LLM inside.

Only the typed errors below may cross the tool boundary; the graph's `tools` node
catches them so a failed tool never crashes the turn.
"""

from __future__ import annotations


class ToolUnavailable(Exception):
    """The tool's backing service is down/over-quota (degrade gracefully)."""


class ToolBadInput(Exception):
    """The tool was called with invalid arguments."""


from .registry import Tool, build_tool_registry  # noqa: E402

__all__ = ["ToolUnavailable", "ToolBadInput", "Tool", "build_tool_registry"]
