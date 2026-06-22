# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A Master IT 2026 project: the **Multilingual Smart Airport Wayfinding Assistant**
(case study: Sheikh Zayed International Airport, AUH). It is an agentic, voice+text
assistant that guides airport passengers in Arabic/Darija/French/English.

The system is specified in Technical Design Documents (`docs/tdd/`). Built so far:
the fine-tuned **ASR** (`asr_finetuning/`, the graded ML contribution), the
**FastAPI backend** (`backend/`, with AirLabs flight data), the **Next.js
frontend** (`frontend/`), and the **LangGraph agent** (TDD-02, `backend/app/agent/`,
on by default; the LLM sits behind a provider interface — offline/no-key by
default, Groq/OpenAI when a key is set), and the **knowledge base + RAG** (TDD-04,
`backend/app/kb/`): a per-`airport_id` data pack with map-graph directions, a
service index, and ChromaDB+multilingual-embedding FAQ retrieval, exposed as the
agent's `directions`/`find_service`/`faq` tools and a `/map` endpoint, and **TTS** (TDD-05,
`backend/app/services/tts.py`): real local MMS-TTS neural voices (on-CPU, no key).
The backend runs every component for real; the **evaluation** harness
(`evaluation/`, TDD-08) scores it reproducibly, and the system is **containerized**
(`deploy/`, TDD-09). All ten TDDs are built.
**`docs/PROGRESS.md` has the live status board — read it first.**

## Read these first (the project's source of truth)

- `docs/PROGRESS.md` — **cross-session state**: component status board, key
  decisions, open questions, and a dated session log. **Read it at the start of a
  session and update it at the end** (add a session-log entry + update the status
  table). This is how work continues across sessions.
- `docs/tdd/README.md` → `docs/tdd/TDD-00-System-Overview.md` — architecture,
  end-to-end request flow, and component contracts. Each component has its own
  `TDD-0X-*.md` with a task checklist; follow the relevant one when building it.
- `PROJECT_REQUIREMENTS.md` — the supervisor's grading requirements.

## Consistency rule (non-negotiable)

**Every decision or change must be propagated to ALL places that describe it, in
the same change — never leave one source stale.** A fact (a chosen dataset, a
column name, a hyperparameter, an API provider, a contract) is almost always
written in more than one file. When you change it in one, grep for every other
occurrence and update them too, before committing.

Concretely, when a change touches any of these, check **all** the rows that apply:

| If you change… | Also update… |
|---|---|
| Code behavior (`asr_finetuning/src/*`) | the module's `README.md`, the relevant `docs/tdd/TDD-0X-*.md`, and any config comment that describes it |
| A config value/field (`config/*.yaml`) | the inline comment, `asr_finetuning/README.md`, and the owning TDD |
| A dataset / model / provider choice | `docs/PROGRESS.md` (decisions + open questions), the owning TDD, `README.md`, and the config preset |
| A component design or contract | its `TDD-0X`, `TDD-00` if cross-cutting, and `docs/tdd/README.md` status |
| A non-negotiable invariant or the git workflow | this file, `.cursor/rules/`, **and** `AGENTS.md` (the project is also developed in Cursor and Codex — keep all three AI guides in sync) |
| Anything notable this session | `docs/PROGRESS.md` session log + status table |
| Branch contents (after a push) | the **PR description** — it is the canonical spec; rewrite it clean (audit trail goes in a PR comment) |

**Procedure:** after any change, run a repo-wide grep for the old value
(e.g. `grep -rn "<old-name>"`) to prove no stale copy survives — the way the
`darija_ar → darija_Arab_new` rename was swept across README, TDD-01, and
PROGRESS. "I updated the code but not the docs" is a defect, not a follow-up.

## Non-negotiable project constraint

The supervisor requires an **owned/fine-tuned model, not just calls to a hosted
API**. The graded ML contribution is the **fine-tuned Whisper** model
(`asr_finetuning/`). The LLM, TTS, and flight-data services are intentionally
external APIs (infrastructure). Do not "simplify" the project by replacing the
fine-tuned Whisper with a hosted speech API — that defeats its purpose.

Two further cross-cutting rules from TDD-00 that any new component must honor:
- **Airport-agnostic**: never hard-code airport facts (gates, services, AUH).
  Airport-specific data lives in the knowledge base keyed by `airport_id`.
- **Language is first-class**: carry an explicit language code (`ar`, `ary`
  Darija, `fr`, `en`) across boundaries; the assistant replies in the user's
  language.

## The one implemented component: `asr_finetuning/`

Fine-tunes `openai/whisper-small` for Darija/Arabic speech (Hugging Face
`Seq2SeqTrainer`). Design: `docs/tdd/TDD-01-ASR-Whisper.md`; usage:
`asr_finetuning/README.md`.

Run everything **from the `asr_finetuning/` directory** (modules use the `src.`
package prefix). Training needs a GPU (Colab/Kaggle) — this is not runnable on a
CPU-only box.

```bash
cd asr_finetuning
pip install -r requirements.txt
huggingface-cli login                 # gated datasets (e.g. Common Voice)

bash scripts/smoke_test.sh            # 5-step end-to-end sanity run
python -m src.train --config config/default.yaml
python -m src.evaluate_model --config config/default.yaml --model.name <ckpt_or_hub_id>
python -m src.transcribe --model.name <ckpt> --audio clip.wav
```

Config: `config/default.yaml` holds all hyperparameters. **Override any field on
the CLI with dotted keys** (handled by `src/config.py`), e.g.
`--training.max_steps 5000 --dataset.config ar --model.name openai/whisper-medium`.

Module roles: `config.py` (YAML + dotted-CLI loader) · `data.py` (HF dataset load,
preprocessing, the speech seq2seq data collator) · `metrics.py` (WER/CER) ·
`train.py` (entry point) · `evaluate_model.py` (base-vs-fine-tuned eval) ·
`transcribe.py` (`WhisperTranscriber`, the serving interface the backend will call).

There is no test framework wired up; `scripts/smoke_test.sh` is the de-facto
end-to-end check. The config loader can be exercised directly by importing
`src.config.load_config`.

## Target architecture (per TDD-00)

Pipeline: **frontend (Next.js)** → **FastAPI backend** orchestrates **STT
(fine-tuned Whisper)** → **LLM agent (LangGraph)** → **tools (flight API) / RAG
knowledge base (ChromaDB)** → **TTS (local MMS-TTS)** → response. Built: `backend/`
(TDD-06), `frontend/` (TDD-07), the agent in `backend/app/agent/` (TDD-02/03, flight
+ KB tools), the knowledge base in `backend/app/kb/` (TDD-04), and TTS in
`backend/app/services/tts.py` (TDD-05). Like the agent, the KB lives **inside the
backend package** (`backend/app/kb/`, not a top-level `knowledge_base/`) since it's
imported with the `app.` prefix and shares the service container. `evaluation/`
(TDD-08) holds the reproducible scoring harness, and `deploy/` holds the Docker
setup (TDD-09): `backend/Dockerfile` + `frontend/Dockerfile` +
`deploy/docker-compose.yml` (light default) + `docker-compose.full.yml` (real
stack) — `docker compose -f deploy/docker-compose.yml up --build`.

## Git workflow

- **One branch + one PR per TDD/component.** When you implement a component,
  cut a dedicated branch off `main` named for its TDD (e.g.
  `feat/tdd-06-backend`, `feat/tdd-02-agent`), do the work there, and open its
  own PR. Keep each PR scoped to a single TDD so reviews stay focused.
- The initial documentation (PROJECT_REQUIREMENTS, the TDD set, PROGRESS,
  CLAUDE.md, and the ASR scaffold) was merged into `main` via **PR #1** — those
  docs stay as-is; do not try to re-split them.
- Small cross-cutting doc/chore updates (like this file or `docs/PROGRESS.md`)
  may go on a short-lived `chore/*` or `docs/*` branch with their own PR.
- Always branch from an up-to-date `main`: `git fetch origin && git switch -c
  feat/tdd-0X-<name> origin/main`. Push with `git push -u origin <branch>`.
