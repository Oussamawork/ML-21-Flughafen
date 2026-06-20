#!/usr/bin/env bash
# PostToolUse(Edit|Write|MultiEdit): format + lint-fix edited Python files with ruff.
# No-op (exit 0) if ruff isn't installed or the file isn't a .py — never blocks edits.
input=$(cat)
file=$(printf '%s' "$input" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
case "$file" in
  *.py)
    if command -v ruff >/dev/null 2>&1 && [ -f "$file" ]; then
      ruff format "$file" >/dev/null 2>&1
      ruff check --fix "$file" >/dev/null 2>&1
    fi
    ;;
esac
exit 0
