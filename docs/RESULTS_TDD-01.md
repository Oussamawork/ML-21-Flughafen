# Results — TDD-01: Fine-Tuned Whisper for Moroccan Darija

**Model:** `openai/whisper-small` fine-tuned on Moroccan Darija
**Hub id:** `Amassu/whisper-small-darija`
**Date:** 2026-06-21 · **Hardware:** NVIDIA Tesla T4 (Colab)

This is the project's **owned ML contribution** (per the supervisor's requirement
to fine-tune a model, not just call a hosted API). We fine-tuned Whisper-small on
the Darija Open Dataset (DODa) audio and measured it against the un-tuned base
model on the **same held-out evaluation set**.

---

## Headline result

| Metric | Base `whisper-small` | **Fine-tuned (ours)** | Absolute ↓ | Relative ↓ |
|---|---|---|---|---|
| **WER** | 108.18% | **28.79%** | −79.39 pts | **73.4%** |
| **CER** | 63.76% | **9.63%** | −54.13 pts | **84.9%** |

- Evaluation set: **1,259** Darija utterances, held out via a **sentence-grouped
  split** (no transcript appears in both train and eval, so the score is not
  inflated by DODa's parallel recordings).
- **WER > 100% for the base model is expected** — out of the box, Whisper inserts
  so many spurious words on Darija that the error count exceeds the reference
  length. In practice the base model is **unusable** for Darija.
- A **9.63% CER** from a small model on a low-resource dialect is a strong result.

## Why the base model fails (motivation)

Whisper has no notion of Darija; on the baseline it frequently **switched to the
wrong language entirely**, emitting Chinese or Hindi script for Darija audio:

| Reference (Darija) | Base model output | Fine-tuned output |
|---|---|---|
| كنهضر على مراكش | كان هدر على مراركش | ✅ كنهضر على مراكش |
| واش نتي حمقا ؟ | **我身体很大** *(Chinese)* | واش نتي حمقة *(near-perfect)* |
| قلت ليك الكرافس واش ما كتسمعش ؟ | جدليك رقرافس واشمك اتسمعش | قلت ليك ركرافس واش مكتسمعش |
| ورا عشر سنين هادي | **वरा शर्स्नीन है दी** *(Hindi)* | ✅ ورا عشر سنين هادي |
| حشومة | هل شو ما؟ | ✅ حشومة |

After fine-tuning, the same utterances are transcribed correctly (3/5 exact, 2/5
near-exact). This side-by-side is the core "before/after" evidence.

## Setup

| Item | Value |
|---|---|
| Base model | `openai/whisper-small` (244M params) |
| Language / task | `arabic` / `transcribe` |
| Dataset | `atlasia/DODa-audio-dataset` (DODa, ~9h46m, 12,743 clips) |
| Target column | `darija_Arab_new` (Arabic-script transcription) |
| Split | train-only on the Hub → 10% sentence-grouped held-out eval (1,259 samples; 22 null-transcript rows dropped) |
| Training config | `asr_finetuning/config/doda_darija.yaml` — `max_steps=3000`, `batch=16`, `lr=1e-5`, `warmup=300`, `fp16`, best-checkpoint-by-WER |
| Metrics | WER (primary), CER — via `jiwer`/`evaluate` |
| Reproduce | `python -m src.evaluate_model --config config/doda_darija.yaml --model.name <base|ckpt>` |

## How to reproduce the comparison

```bash
cd asr_finetuning
# baseline
python -m src.evaluate_model --config config/doda_darija.yaml --model.name openai/whisper-small
# fine-tuned
python -m src.evaluate_model --config config/doda_darija.yaml --model.name Amassu/whisper-small-darija
```

## Notes / limitations

- The model reports language `arabic` (Whisper has no Darija token); Darija rides
  under the Arabic tag. Distinguishing Darija vs MSA at the language level is a
  possible stretch (dialect classifier).
- ~10h of audio is modest; more data (mixing DVoice / Common Voice Arabic) would
  likely lower WER further.
- _To add when available:_ WER-vs-steps training curve (from
  `trainer_state.json`) and wall-clock training time.
