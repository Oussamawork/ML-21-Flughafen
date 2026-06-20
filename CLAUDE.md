# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A Master IT 2026 project: the **Multilingual Smart Airport Wayfinding Assistant**
(case study: Sheikh Zayed International Airport, AUH). It is an agentic, voice+text
assistant that guides airport passengers in Arabic/Darija/French/English.

The repo is currently **documentation-first**: the full system is specified in
Technical Design Documents, and only one component (the ASR/speech-to-text
pipeline) is implemented so far. Most "components" below exist as designs, not code.

## Read these first (the project's source of truth)

- `docs/PROGRESS.md` — **cross-session state**: component status board, key
  decisions, open questions, and a dated session log. **Read it at the start of a
  session and update it at the end** (add a session-log entry + update the status
  table). This is how work continues across sessions.
- `docs/tdd/README.md` → `docs/tdd/TDD-00-System-Overview.md` — architecture,
  end-to-end request flow, and component contracts. Each component has its own
  `TDD-0X-*.md` with a task checklist; follow the relevant one when building it.
- `PROJECT_REQUIREMENTS.md` — the supervisor's grading requirements.

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

## Target architecture (per TDD-00, mostly not yet built)

Pipeline: **frontend (Next.js)** → **FastAPI backend** orchestrates **STT
(fine-tuned Whisper)** → **LLM agent (LangGraph)** → **tools (flight API) / RAG
knowledge base (ChromaDB)** → **TTS** → response. Planned top-level dirs (create
when implementing the matching TDD): `agent/` (TDD-02/03), `knowledge_base/`
(TDD-04), `speech/` (TDD-05), `backend/` (TDD-06), `frontend/` (TDD-07),
`evaluation/` (TDD-08), `deploy/` (TDD-09).

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
