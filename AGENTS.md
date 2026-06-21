# AGENTS.md

Agent instructions for this repo (read by OpenAI Codex CLI and other AGENTS.md-aware
tools). It **mirrors `CLAUDE.md`** (Claude Code) and `.cursor/rules/` (Cursor) — the
three are kept in sync; this file stays thin and points at the authoritative docs.

## What this is

A Master IT 2026 project: the **Multilingual Smart Airport Wayfinding Assistant**
(case study: Sheikh Zayed Intl, AUH) — an agentic voice+text assistant guiding
passengers in Arabic/Darija/French/English.

## Read these first (authoritative, kept current)

- **`CLAUDE.md`** — the full repo guide (commands, architecture, workflow).
- **`docs/PROGRESS.md`** — cross-session status board, decisions, open questions,
  dated session log. **Read at session start; update at session end** (status
  table + a session-log entry).
- **`docs/tdd/README.md` → `docs/tdd/TDD-00-System-Overview.md`** — architecture,
  request flow, component contracts; each component has its own `TDD-0X-*.md`.
- **`PROJECT_REQUIREMENTS.md`** — the supervisor's grading requirements.

## Non-negotiable invariants

1. **Owned/fine-tuned model, not just a hosted API.** The graded ML contribution
   is the fine-tuned Whisper in `asr_finetuning/` (`Amassu/whisper-small-darija`).
   The LLM, TTS, and flight data (AirLabs) are external infrastructure by design —
   do not replace the fine-tuned Whisper with a hosted speech API.
2. **Airport-agnostic** — never hard-code airport facts; key data by `airport_id`
   (defaults to `AUH`).
3. **Language is first-class** — carry `ar`/`ary`/`fr`/`en` across boundaries;
   reply in the user's language; render RTL for Arabic/Darija.
4. **Flight/ticket number is a typed structured field, never parsed from audio.**
5. **Secrets server-side only** — the AirLabs key lives in the backend; the
   frontend never calls AirLabs directly; never commit keys.

## Consistency rule (non-negotiable)

Propagate every change to **all** places that describe it, in the same change:
code, config comments, the module `README.md`, the owning `docs/tdd/TDD-0X-*.md`,
`docs/PROGRESS.md`, `docs/tdd/README.md`, the **PR description**, and — for an
invariant or workflow change — `CLAUDE.md`, `.cursor/rules/`, and this file. After
a change, `grep -rn "<old-value>"` to prove no stale copy survives.

## Commands

```bash
# ASR (the owned model) — run from asr_finetuning/ ; GPU needed for training
cd asr_finetuning && pip install -r requirements.txt
python -m src.train --config config/doda_darija.yaml
python -m src.evaluate_model --config config/doda_darija.yaml --model.name <ckpt_or_hub_id>

# Backend (FastAPI) — runs with offline stubs (no GPU/keys)
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd backend && pytest

# Frontend (Next.js)
cd frontend && npm install && npm run dev      # backend must be running
cd frontend && npm run typecheck               # keep green
```

## Git workflow

**One branch + one PR per TDD/component**, cut from an up-to-date `main`
(e.g. `feat/tdd-02-agent`). Small cross-cutting chores → a `chore/*` / `docs/*`
branch. The PR description is the canonical spec.
