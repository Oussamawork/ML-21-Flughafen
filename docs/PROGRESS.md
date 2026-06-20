# Project Progress Log

Cross-session source of truth for **what's done, what's next, and key decisions**.
Update this at the end of every working session so any future session (human or
AI) can resume without re-reading everything.

**Project:** Multilingual Smart Airport Wayfinding Assistant (case study: AUH)
**Branch:** `fix/tdd-01-doda-loader-smoke`

---

## 1. Component status

Legend: ⚪ Not started · 🟡 In progress · 🟢 Done · 🔵 Blocked

| Component | TDD | Status | Notes |
|---|---|---|---|
| System overview / architecture | TDD-00 | 🟢 | Design written |
| STT — fine-tuned Whisper | TDD-01 | 🟡 | Pipeline built; DODa wired; smoke test passes (CPU); **full GPU train pending** |
| LLM agent (LangGraph) | TDD-02 | ⚪ | Designed |
| Agent tools + flight API | TDD-03 | ⚪ | Designed |
| Knowledge base + RAG | TDD-04 | ⚪ | Designed |
| TTS | TDD-05 | ⚪ | Designed |
| Backend API (FastAPI) | TDD-06 | ⚪ | Designed |
| Frontend (Next.js) | TDD-07 | ⚪ | Designed |
| Evaluation | TDD-08 | ⚪ | Designed |
| Deployment (Docker) | TDD-09 | ⚪ | Designed |

**Milestones:** M1 Speech-in · M2 Brain · M3 Knowledge · M4 Speech-out+UI ·
M5 Eval+Deploy. → Currently inside **M1**.

## 2. Key decisions (chronological)

- **2026-06-20** Domain confirmed: airport wayfinding (not pharmacy); cleared with
  supervisor. Repo name "Flughafen" = airport.
- **2026-06-20** Owned ML contribution = **fine-tuned Whisper (Darija/Arabic)** to
  satisfy "fine-tune, don't just call an API". LLM/TTS/flight data stay as
  external APIs (infrastructure).
- **2026-06-20** Whisper base = **whisper-small**; dataset = public HF
  (configurable), default Common Voice Arabic; metric WER+CER.
- **2026-06-20** Documentation approach: one TDD per component (TDD-00…09) +
  this progress log. All written in full detail upfront.
- **2026-06-20** PR #1 (initial docs + ASR scaffold) merged into `main`.
- **2026-06-20** Workflow: **one branch + one PR per TDD/component** going
  forward. Each implementation gets a dedicated branch off `main`
  (e.g. `feat/tdd-06-backend`) with its own scoped PR. Merged TDD docs stay as-is.

## 3. Open questions / to resolve

- [x] ~~Verify a real **Darija ASR dataset**~~ → chose `atlasia/DODa-audio-dataset`
      (DODa, ~9h46m), wired as `config/doda_darija.yaml`. Schema confirmed on the
      Hub: `train` split only; Arabic-script column `darija_Arab_new`. Eval set is
      carved from train with a sentence-grouped split (no leakage). Dataset is gated.
- [ ] LLM choice for the agent: GPT-4o-mini (default) vs Llama 3.1 via Groq.
- [ ] Flight API provider that actually returns **gate/terminal** for AUH on free
      tier (else seed gates in KB for case-study flights).
- [ ] Where to run Whisper in the deployed demo (CPU latency vs hosted STT).

## 4. Session log

### Session 2026-06-20
- Read supervisor's project brief → `PROJECT_REQUIREMENTS.md` (committed).
- Analyzed Wayfinding proposal; flagged the "must fine-tune" gap → chose Whisper.
- Built `asr_finetuning/` pipeline (config, data, train, eval, transcribe) +
  README; config loader unit-tested locally (no GPU here).
- Saved proposal (`docs/Proposition_Projet_Wayfinding.md`) + ASR plan
  (`docs/PLAN_ASR_Whisper.md`).
- Wrote full TDD set `docs/tdd/TDD-00…09` + this progress log.
- **Next session:** verify Darija dataset; run baseline + smoke test on a GPU
  (Colab/Kaggle); then start TDD-02 agent scaffold.

### Session 2026-06-20 (cont.) — TDD-01 Darija dataset
- Researched Darija ASR datasets on the HF Hub (PR #1, #2 already merged).
- Chose **DODa** (`atlasia/DODa-audio-dataset`) as primary Darija set; added
  `config/doda_darija.yaml`. Documented alternatives (DVoice, Darija-Wiki, FLEURS).
- Hardened `data.load_splits`: auto-carve validation split when none exists;
  fail-fast with available columns on a mismatch. Added `dataset.test_size`.
- Updated ASR README, TDD-01, PROGRESS. Branch `feat/tdd-01-darija-dataset`.
- **Next:** verify DODa column names/splits in the HF viewer, then baseline +
  smoke test on a GPU.

### Session 2026-06-20 (cont.) — TDD-01 training notebook
- PR #4 merged. Added click-to-run Colab/Kaggle notebook
  `asr_finetuning/notebooks/finetune_whisper_colab.ipynb` (GPU check → clone →
  install → HF login → smoke test → baseline eval → fine-tune → eval → push to
  Hub → listen test). Works in browser Colab and the VS Code Colab extension.
- Linked it from the ASR README; ticked the notebook item in TDD-01.
- Branch `feat/tdd-01-colab-notebook`. **Next:** run it on a T4 to get the
  base-vs-fine-tuned WER, then wire `WhisperTranscriber` into TDD-06.

### Session 2026-06-21 — TDD-01 loader + smoke-test fixes
- Fixed DODa load crash: filter ~22 null `darija_Arab_new` rows before grouped split.
- Hardened audio loading (`decode=False` + soundfile/librosa) for Mac CPU / no FFmpeg.
- Pointed `scripts/smoke_test.sh` at DODa (Common Voice 17 broken on `datasets>=4`).
- Updated Colab notebook clone cell (git pull + hotfix). Smoke test verified locally.
- Branch `fix/tdd-01-doda-loader-smoke`. **Next:** full fine-tune on Colab T4.

<!-- Template for new sessions:
### Session YYYY-MM-DD
- Did: ...
- Decisions: ...
- Next: ...
-->

## 5. How to resume (quick start for a new session)

1. Read this file + `docs/tdd/TDD-00-System-Overview.md`.
2. Check "Component status" + the current milestone.
3. Open the TDD for the component you're working on; follow its task checklist.
4. Do the work; update the component's status here + add a session-log entry.
5. Commit + push to the branch above.
