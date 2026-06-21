"""Pytest bootstrap — keep the default test suite on stub STT (no GPU/model)."""

from __future__ import annotations

import os

# Must run before `app.config` is imported by test modules.
os.environ["LOAD_STT"] = "false"
