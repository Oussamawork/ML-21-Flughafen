# TDD-01 — Speech-to-Text: Fine-Tuned Whisper (Darija/Arabic)

**Component:** `asr_finetuning/` + STT serving glue
**Status:** 🟢 Pipeline built · ⚪ Not yet trained
**Depends on:** none (upstream of the agent) · **Consumed by:** TDD-06 (`/transcribe`)

> This TDD formalizes `../PLAN_ASR_Whisper.md`. It is the project's **owned ML
> contribution**: a Whisper model fine-tuned for Moroccan Darija / Arabic.

---

## 1. Purpose

Convert a passenger's spoken request (Arabic / Darija / French / English) into
text for the agent. Generic hosted ASR transcribes Darija poorly; we fine-tune
Whisper on Darija/Arabic speech and report the WER/CER improvement vs. the base
model as the headline ML result.

## 2. Requirements satisfied

- *Fine-tune/adapt a model rather than only calling an API* (supervisor's core ask).
- *Multilingual STT/TTS pipeline with Darija support* (proposal objective).
- *Implementation of NLP/speech components* + *dataset preparation* + *evaluation*
  (rubric deliverables).

## 3. Design

### 3.1 Model
- Base: `openai/whisper-small` (244M). Fits a free Colab/Kaggle T4 (16 GB).
- Language token: `arabic` (Whisper has no Darija token; Darija rides under
  Arabic). `task=transcribe`.
- Stretch: `whisper-medium` if accuracy is insufficient and an A100 is available.

### 3.2 Pipeline (implemented)
```
HF dataset ─▶ resample 16kHz ─▶ log-Mel features ─▶ tokenize text
            ─▶ filter >30s ─▶ Seq2SeqTrainer (fp16, gen-eval) ─▶ best-by-WER ckpt
            ─▶ evaluate (base vs FT) ─▶ WhisperTranscriber (serving)
```
Files (already in repo):
- `config/default.yaml` — all hyperparameters.
- `src/config.py` — YAML + dotted-CLI override loader.
- `src/data.py` — dataset load, preprocessing, `DataCollatorSpeechSeq2SeqWithPadding`.
- `src/metrics.py` — WER + CER.
- `src/train.py` — fine-tuning entry point (`Seq2SeqTrainer`).
- `src/evaluate_model.py` — evaluate any checkpoint on a split.
- `src/transcribe.py` — `WhisperTranscriber` inference helper.

### 3.3 Data strategy
- **Darija (primary):** `atlasia/DODa-audio-dataset` — ~9h46m / 12,743 parallel
  clips from the published *Darija Open Dataset*, with Arabic-script + Latin
  transcriptions. Wired as `config/doda_darija.yaml` using the `darija_Arab_new`
  Arabic-script column. This is the recommended fine-tuning set; best aligned with
  the airport use case.
- **Baseline / coverage:** Common Voice Arabic
  (`mozilla-foundation/common_voice_17_0`, config `ar`) — mostly MSA.
  `config/default.yaml`. **Note:** CV17 needs the script loader removed in
  `datasets>=4`; `requirements.txt` pins `datasets<4` so the default config loads.
  DODa/FLEURS load on any datasets version.
- **Alternatives:** `aioxlabs/dvoice-darija` (DVoice), 
  `atlasia/Moroccan-Darija-Wiki-Audio-Dataset` (small, clean — good for eval).
- **Loader robustness:** datasets without an eval split auto-carve a `test_size`
  validation set, **split by sentence** so the same transcript never lands in both
  train and eval (DODa has parallel recordings); rows with null/blank transcripts
  are dropped before the split (~22 in DODa); missing columns fail fast listing
  available columns. Audio is loaded via soundfile/librosa (`decode=False`) so
  the pipeline runs on Mac CPU without torchcodec/FFmpeg.
- **DODa schema (confirmed on the Hub):** `train` split only; columns `audio`
  (16 kHz), `darija_Arab_new`/`darija_Arab_old`, `darija_Latn`, `english`. Dataset
  is gated — accept terms + `huggingface-cli login` before training.
- Optional text normalization (punctuation/casing) configurable.

### 3.4 Training defaults
`lr=1e-5`, `warmup=500`, `max_steps=4000`, `bs=16` (+grad-accum), `fp16`,
`eval_steps=500`, best-model-by-WER checkpointing. All overridable via CLI.

## 4. Interfaces & data contracts

### 4.1 Serving interface (consumed by the backend)
```python
class WhisperTranscriber:
    def __init__(self, model_name: str, language="arabic", task="transcribe",
                 device: str | None = None): ...
    def transcribe(self, audio: str | "np.ndarray", sampling_rate: int = 16000) -> str
```
- `audio`: file path or 1-D float array @ 16 kHz mono.
- returns: transcript string (Arabic script for ar/ary).

### 4.2 Backend endpoint (defined fully in TDD-06)
`POST /transcribe` · multipart audio → `{ "text": str, "language": str }`
- Language detection: Whisper's detected language token, mapped to `ar/ary/fr/en`.
  (Darija vs MSA disambiguation is heuristic; see risks.)

## 5. Evaluation

- Metrics: **WER** (primary), **CER** (fairer for Arabic morphology).
- Protocol: held-out Darija/Arabic test split; report **base vs. fine-tuned**.
- Deliverable artifact: a results table + 5 qualitative REF/PRED examples
  (`evaluate_model.py` prints both). Target: meaningful WER reduction vs base.

## 6. Dependencies

`torch, transformers, datasets, accelerate, evaluate, jiwer, librosa, soundfile,
PyYAML, tensorboard, huggingface_hub` (see `asr_finetuning/requirements.txt`).
GPU required for training (Colab/Kaggle); CPU is fine for inference of small model.

## 7. Open questions / risks

- **Darija data scarcity** → may need to combine sources or record a small set.
- **Darija vs MSA language tag** → Whisper returns "arabic" for both; if the UI
  needs to distinguish, add a lightweight dialect classifier (stretch).
- **Overfitting** on small Darija sets → rely on held-out eval + best-ckpt.
- **Latency** of whisper-small on CPU in the demo → may serve on GPU or batch.

## 8. Task checklist

- [x] Configurable fine-tuning pipeline
- [x] Config-loader unit-tested
- [x] Select Darija dataset (DODa) + add `config/doda_darija.yaml` preset
- [x] Loader robustness: auto eval-split + fail-fast on missing columns
- [x] Verify DODa column names/splits on the HF Hub (train-only; `darija_Arab_new`)
- [x] Colab/Kaggle click-to-run notebook (`notebooks/finetune_whisper_colab.ipynb`)
- [x] Smoke test passes locally (Mac CPU + DODa; `scripts/smoke_test.sh`)
- [x] Full fine-tune (3000 steps on a T4)
- [x] Evaluate fine-tuned; record delta — **WER 108.18% → 28.79%; CER 63.76% → 9.63%** (see `../RESULTS_TDD-01.md`)
- [x] Push checkpoint to HF Hub — [`Amassu/whisper-small-darija`](https://huggingface.co/Amassu/whisper-small-darija)
- [ ] Wire `WhisperTranscriber` into `/transcribe` (TDD-06) via `LOAD_STT=true`
