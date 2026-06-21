---
language:
- ar
license: apache-2.0
base_model: openai/whisper-small
tags:
- whisper
- automatic-speech-recognition
- darija
- moroccan-arabic
- asr
datasets:
- atlasia/DODa-audio-dataset
metrics:
- wer
- cer
model-index:
- name: whisper-small-darija
  results:
  - task:
      type: automatic-speech-recognition
      name: Automatic Speech Recognition
    dataset:
      name: DODa-audio-dataset (held-out)
      type: atlasia/DODa-audio-dataset
    metrics:
    - type: wer
      value: 28.79
      name: WER
    - type: cer
      value: 9.63
      name: CER
---

# whisper-small-darija

Fine-tuned [`openai/whisper-small`](https://huggingface.co/openai/whisper-small)
for **Moroccan Darija** speech recognition. Built as the speech-to-text component
of a Multilingual Smart Airport Wayfinding Assistant (Master IT 2026).

## Results

On a held-out, **sentence-grouped** split of `atlasia/DODa-audio-dataset`
(1,259 utterances):

| Metric | Base `whisper-small` | This model | Relative ↓ |
|---|---|---|---|
| WER | 108.18% | **28.79%** | 73.4% |
| CER | 63.76% | **9.63%** | 84.9% |

The base model is effectively unusable on Darija (it often emits the wrong script
entirely, e.g. Chinese/Hindi). Fine-tuning makes transcription reliable.

## Usage

```python
from transformers import WhisperForConditionalGeneration, WhisperProcessor
import librosa

model = WhisperForConditionalGeneration.from_pretrained("Amassu/whisper-small-darija")
processor = WhisperProcessor.from_pretrained("Amassu/whisper-small-darija",
                                             language="arabic", task="transcribe")

audio, _ = librosa.load("clip.wav", sr=16000, mono=True)
feats = processor.feature_extractor(audio, sampling_rate=16000, return_tensors="pt").input_features
ids = model.generate(feats, language="arabic", task="transcribe")
print(processor.batch_decode(ids, skip_special_tokens=True)[0])
```

## Training

- **Base:** `openai/whisper-small` (244M)
- **Data:** `atlasia/DODa-audio-dataset` (DODa, ~9h46m), Arabic-script column
  `darija_Arab_new`
- **Config:** `max_steps=3000`, batch 16, lr 1e-5, warmup 300, fp16,
  best-checkpoint-by-WER (HF `Seq2SeqTrainer`)
- **Eval:** 10% sentence-grouped held-out split (no transcript leakage)
- **Hardware:** NVIDIA Tesla T4 (Colab)

Pipeline & reproduction: <https://github.com/Oussamawork/ML-21-Flughafen> (`asr_finetuning/`).

## Limitations

- Reports language `arabic` (Whisper has no Darija token).
- ~10h of training audio is modest; more data would improve robustness.
