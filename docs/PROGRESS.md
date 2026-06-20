# Project Progress Log

Cross-session source of truth for **what's done, what's next, and key decisions**.
Update this at the end of every working session so any future session (human or
AI) can resume without re-reading everything.

**Project:** Multilingual Smart Airport Wayfinding Assistant (case study: AUH)
**Branch:** `claude/professor-projects-analysis-t99iau`

---

## 1. Component status

Legend: ⚪ Not started · 🟡 In progress · 🟢 Done · 🔵 Blocked

| Component | TDD | Status | Notes |
|---|---|---|---|
| System overview / architecture | TDD-00 | 🟢 | Design written |
| STT — fine-tuned Whisper | TDD-01 | 🟡 | Pipeline built & config-tested; **not trained yet** |
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

## 3. Open questions / to resolve

- [ ] Verify a real **Darija ASR dataset** on the HF Hub; update
      `asr_finetuning/config/default.yaml`.
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
