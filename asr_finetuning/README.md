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

```bash
# 0. Sanity check the pipeline (few samples, 5 steps)
bash scripts/smoke_test.sh

# 1. Full fine-tune with defaults (whisper-small, Common Voice Arabic)
python -m src.train --config config/default.yaml

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
`dataset.config`, mapping its audio + transcript columns to canonical names.

| Dataset | `name` / `config` | Notes |
|---|---|---|
| **Common Voice (Arabic)** *(default)* | `mozilla-foundation/common_voice_17_0` / `ar` | Reliable, gated (accept terms + login). Mostly MSA. |
| **FLEURS (Arabic)** | `google/fleurs` / `ar_eg` | Clean read speech, good for a baseline. |
| **Darija-specific sets** | *verify on the HF Hub* | Darija ASR corpora exist but vary in availability/quality; search the Hub (e.g. "darija asr", "moroccan") and set `name`/`config`/`audio_column`/`text_column` accordingly. Best aligned with the airport use case. |

> ⚠️ Darija dataset IDs change over time — **verify availability on the Hub
> before training** and update `config/default.yaml`. Mixing an MSA set (Common
> Voice) with a Darija set gives the best coverage for code-mixed airport speech.

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
