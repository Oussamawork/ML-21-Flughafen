"""Pytest bootstrap — keep the default test suite on stub STT (no GPU/model)."""

from __future__ import annotations

import os

# Must run before `app.config` is imported by test modules. These override any
# local backend/.env so the suite stays offline (no GPU, no LLM key, no network).
os.environ["LOAD_STT"] = "false"
os.environ["LLM_PROVIDER"] = "offline"
