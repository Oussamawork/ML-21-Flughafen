"""Lightweight config loading: YAML file + dotted CLI overrides."""
from __future__ import annotations

import argparse
import copy
from typing import Any

import yaml


def _set_dotted(d: dict, dotted_key: str, value: Any) -> None:
    """Set d["a"]["b"] from key "a.b", creating intermediate dicts as needed."""
    keys = dotted_key.split(".")
    cur = d
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = value


def _coerce(value: str) -> Any:
    """Best-effort string -> python type for CLI overrides."""
    lowered = value.lower()
    if lowered in {"none", "null"}:
        return None
    if lowered in {"true", "false"}:
        return lowered == "true"
    for cast in (int, float):
        try:
            return cast(value)
        except ValueError:
            continue
    return value


def load_config(argv: list[str] | None = None) -> dict:
    """Parse --config plus arbitrary --section.key value overrides."""
    parser = argparse.ArgumentParser(
        description="Fine-tune / evaluate Whisper for Darija/Arabic ASR.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--config",
        default="config/default.yaml",
        help="Path to the YAML config file.",
    )
    known, extras = parser.parse_known_args(argv)

    with open(known.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    config = copy.deepcopy(config)

    # Parse remaining "--dotted.key value" pairs as overrides.
    i = 0
    while i < len(extras):
        token = extras[i]
        if not token.startswith("--"):
            raise SystemExit(f"Unexpected argument: {token}")
        key = token[2:]
        if "=" in key:
            key, raw = key.split("=", 1)
        else:
            i += 1
            if i >= len(extras):
                raise SystemExit(f"Missing value for --{key}")
            raw = extras[i]
        _set_dotted(config, key, _coerce(raw))
        i += 1

    config["_config_path"] = known.config
    return config
