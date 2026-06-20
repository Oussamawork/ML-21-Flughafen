# ASR Fine-Tuning — Darija/Arabic Whisper

Fine-tunes **OpenAI Whisper** for **Moroccan Darija / Arabic** speech recognition.
This is the *owned, fine-tuned ML component* of the **Multilingual Smart Airport
Wayfinding Assistant** — it replaces a generic hosted speech API so the project
satisfies the supervisor's requirement to *adapt a model, not just call an API*
(see `../PROJECT_REQUIREMENTS.md`).

The resulting model is consumed by the agent's Speech-to-Text tool via
`src/transcribe.py::WhisperTranscriber`.

## Why fine-tune Whisper?

Whisper has no dedicated *Darija* language; Darija audio is transcribed under the
`arabic` token and out-of-the-box accuracy on Moroccan Darija is poor (Darija is
under-represented in pre-training). Fine-tuning on Darija/Arabic speech is a
concrete, measurable ML contribution (reported as WER/CER improvement vs. the
base model).

## Layout

```
asr_finetuning/
├── config/default.yaml      # all hyperparameters & dataset settings
├── src/
│   ├── config.py            # YAML + dotted CLI override loader
│   ├── data.py              # dataset loading, preprocessing, data collator
│   ├── metrics.py           # WER / CER
│   ├── train.py             # fine-tuning entry point
│   ├── evaluate_model.py    # evaluate a checkpoint on a split
│   └── transcribe.py        # inference helper used by the agent
└── scripts/smoke_test.sh    # 5-step end-to-end sanity run
```

## Setup

```bash
cd asr_finetuning
pip install -r requirements.txt
# For gated datasets (e.g. Common Voice) accept the terms on the dataset page, then:
huggingface-cli login
```

> **Compute:** `whisper-small` fine-tunes on a single free **Colab/Kaggle T4
> (16 GB)**. This repo's container has no GPU — run training on Colab/Kaggle or a
> GPU machine.

## Quickstart

> **No GPU?** The easiest path is the click-to-run notebook
> [`notebooks/finetune_whisper_colab.ipynb`](notebooks/finetune_whisper_colab.ipynb):
> open it in **browser Colab** *or* **VS Code (Google Colab extension)**, pick a
> free **T4 GPU**, and run the cells (GPU check → clone → install → HF login →
> smoke test → baseline eval → fine-tune → eval → push to Hub). The cells just
> call the `src.*` scripts below.

```bash
# 0. Sanity check the pipeline (few samples, 5 steps)
bash scripts/smoke_test.sh

# 1a. Full fine-tune with defaults (whisper-small, Common Voice Arabic)
python -m src.train --config config/default.yaml

# 1b. Darija fine-tune (whisper-small, DODa) — the recommended Darija run
python -m src.train --config config/doda_darija.yaml

# 2. Override anything from the CLI (dotted keys)
python -m src.train --config config/default.yaml \
    --dataset.config ar --training.max_steps 5000 --training.learning_rate 8e-6

# 3. Evaluate a checkpoint (base vs. fine-tuned — report both in the paper)
python -m src.evaluate_model --config config/default.yaml \
    --model.name openai/whisper-small                    # baseline
python -m src.evaluate_model --config config/default.yaml \
    --model.name ./outputs/whisper-small-darija          # fine-tuned

# 4. Transcribe a clip (what the agent calls at inference time)
python -m src.transcribe --model.name ./outputs/whisper-small-darija --audio clip.wav
```

## Datasets

The pipeline loads any Hugging Face audio dataset via `dataset.name` /
`dataset.config`, mapping its audio + transcript columns to canonical names. If a
dataset has no eval split, set `dataset.eval_split: null` and the loader carves a
`test_size` validation set out of train — split **by sentence**, so the same
transcript never appears in both train and eval (avoids leaking parallel
recordings). Missing columns fail fast with the list of available columns.

Two configs are provided:
- `config/default.yaml` — **Common Voice Arabic** baseline (reliable, mostly MSA).
- `config/doda_darija.yaml` — **DODa Darija** preset (the recommended Darija run).

| Dataset | `name` / `config` | Hours / size | Notes |
|---|---|---|---|
| **DODa audio** *(Darija — recommended)* | `atlasia/DODa-audio-dataset` | ~9h46m, 12,743 clips | Moroccan Darija from the published *Darija Open Dataset*. **Schema (confirmed on the Hub):** `train` split only; columns `audio` (16 kHz), `darija_Arab_new`/`darija_Arab_old` (Arabic script), `darija_Latn`, `english`. Preset uses `darija_Arab_new`. Gated — accept terms + login. Best aligned with the use case. |
| **Common Voice (Arabic)** *(default)* | `mozilla-foundation/common_voice_17_0` / `ar` | large | Reliable, gated (accept terms + login). Mostly MSA — good for coverage/baseline. |
| **DVoice Darija** | `aioxlabs/dvoice-darija` | — | Darija ASR corpus (DVoice initiative); alternative Darija source. |
| **Darija Wiki audio** | `atlasia/Moroccan-Darija-Wiki-Audio-Dataset` | 551 clips | Small, clean parallel set; useful for eval or augmentation. |
| **FLEURS (Arabic)** | `google/fleurs` / `ar_eg` | — | Clean read MSA speech; handy baseline. |

> ℹ️ **DODa's schema is confirmed** (see the table above); the preset is wired to
> the real columns. For **other** Darija sets, verify columns/splits on the HF Hub
> before a long run — they vary, and the loader prints available columns on a
> mismatch. For best coverage of code-mixed airport speech, mix a Darija set
> (DODa/DVoice) with Common Voice Arabic.

For your own recordings, point `dataset.*` at a local manifest by loading it as a
HF `dataset` (CSV/JSON with `audio_path`,`text`) — ask and we'll add a manifest
loader branch.

## Evaluation

`train.py` reports **WER** and **CER** on the eval split each `eval_steps` and
writes `final_metrics.txt`. For the report, present **base vs. fine-tuned** WER/CER
on a held-out Darija test set — that delta is the headline result.

## Integration with the assistant

```python
from asr_finetuning.src.transcribe import WhisperTranscriber

stt = WhisperTranscriber("./outputs/whisper-small-darija")  # load once
text = stt.transcribe("passenger_request.wav")              # -> Darija/Arabic text
# feed `text` into the LLM agent (intent + tool calling)
```
