# Plan — Fine-Tuning Whisper for Darija/Arabic ASR

This is the **owned ML contribution** of the Smart Airport Wayfinding Assistant.
It exists so the project satisfies the supervisor's core requirement: *adapt /
fine-tune a model rather than only calling a hosted API*. Everything else in the
stack (flight data, TTS) may stay as external APIs; the speech-recognition brain
is trained by us.

## Goal

Take `openai/whisper-small` and fine-tune it on Darija/Arabic speech so it
transcribes airport-style passenger requests (e.g. *"ayna bawwabati, rihlati
SV-624"*) better than the off-the-shelf model. Success = a measurable **WER/CER
reduction vs. the base model** on a held-out Darija/Arabic test set.

## Decisions (locked)

| Choice | Value | Reason |
|---|---|---|
| Base model | `whisper-small` (244M) | Fits a free Colab/Kaggle T4; good accuracy. |
| Language token | `arabic` | Whisper has no Darija token; Darija rides under Arabic. |
| Data source | Public HF dataset (configurable) | Start with Common Voice Arabic; add Darija sets. |
| Metric | WER (primary) + CER | CER is fairer for Arabic morphology. |
| Compute | Colab/Kaggle GPU | This repo's container has no GPU. |

## Pipeline (built in `asr_finetuning/`)

1. **Load** train/eval splits from a configurable HF dataset (`src/data.py`).
2. **Preprocess** — resample to 16 kHz, extract log-Mel features, tokenize
   transcripts, optional text normalization, filter >30 s clips.
3. **Train** with HF `Seq2SeqTrainer`, `predict_with_generate`, fp16, best-model
   checkpointing on WER (`src/train.py`).
4. **Evaluate** base vs. fine-tuned on the same split (`src/evaluate_model.py`).
5. **Serve** via `WhisperTranscriber` for the agent's STT tool (`src/transcribe.py`).

All hyperparameters live in `config/default.yaml`; override any field with dotted
CLI flags (e.g. `--training.max_steps 5000`).

## Step-by-step execution plan

- [x] Scaffold configurable fine-tuning pipeline (this commit)
- [ ] **Pick & verify dataset(s)** on the HF Hub — a Darija set + Common Voice
      Arabic for coverage; update `config/default.yaml`.
- [ ] **Baseline**: run `evaluate_model` on `whisper-small` (un-tuned) → record WER/CER.
- [ ] **Smoke test**: `scripts/smoke_test.sh` on a GPU to confirm end-to-end.
- [ ] **Full fine-tune** (~4000 steps) on Colab/Kaggle; watch eval WER.
- [ ] **Evaluate fine-tuned** model on the same test set → record WER/CER delta.
- [ ] **Push** the best checkpoint to the HF Hub (optional) for the demo.
- [ ] **Integrate** `WhisperTranscriber` into the agent's STT tool.
- [ ] **Report**: base-vs-fine-tuned table + a few qualitative transcripts.

## Risks / notes

- **Darija data scarcity** — IDs and quality vary; verify on the Hub before
  training. Mixing MSA (Common Voice) + Darija improves code-mixed coverage.
- **Gated datasets** — Common Voice needs accepting terms + `huggingface-cli login`.
- **Overfitting on small Darija sets** — keep eval split held out; use warmup +
  modest `max_steps`; rely on best-model-by-WER checkpointing.

## How this maps to the supervisor's rubric

- *Implementation of NLP/speech components* → the fine-tuned Whisper model.
- *Dataset preparation* → dataset selection/normalization config.
- *Evaluation* → WER/CER, base vs. fine-tuned.
- *API delivery* → `WhisperTranscriber` plugs into the FastAPI agent service.
