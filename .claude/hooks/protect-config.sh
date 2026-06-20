#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit): require confirmation before editing critical files.
# config/default.yaml drives every hyperparameter; requirements.txt pins the stack.
input=$(cat)
file=$(printf '%s' "$input" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
case "$file" in
  */config/default.yaml|*/requirements.txt)
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"This file controls training hyperparameters/dependencies — confirm the change is intentional."}}'
    exit 0
    ;;
esac
exit 0
