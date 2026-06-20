---
name: eval-report
description: Evaluate a fine-tuned Whisper checkpoint on a split and report WER/CER vs. the base model — the supervisor-required ML metric. Invoke as /eval-report <checkpoint-path> [split].
disable-model-invocation: true
---

# eval-report

Wraps `asr_finetuning/src/evaluate_model.py` to produce the metric the project is
graded on: **WER/CER of the fine-tuned model vs. the base Whisper model** on the
same split (see `PROJECT_REQUIREMENTS.md` — the contribution must be a *measurable*
ASR improvement, not just an API call).

## Arguments

- `<checkpoint-path>` (required): path to the fine-tuned checkpoint, e.g.
  `./outputs/whisper-small-darija`.
- `[split]` (optional): dataset split to evaluate (default: the eval split in
  `config/default.yaml`).

## Steps

Run from `asr_finetuning/`:

1. **Fine-tuned model** — evaluate the checkpoint:
   ```bash
   python -m src.evaluate_model --config config/default.yaml \
     --model.name <checkpoint-path>
   ```
   Capture the reported WER and CER.
2. **Base model** — re-run with the base model name from `config/default.yaml`
   (the `model.name` default, e.g. `openai/whisper-small`) so the comparison is
   apples-to-apples (same split, same normalization):
   ```bash
   python -m src.evaluate_model --config config/default.yaml \
     --model.name <base-model-from-config>
   ```
3. Pass any extra `--section.key value` overrides the user supplies straight
   through (the config loader accepts dotted overrides).

## Output

A short markdown table and the absolute + relative improvement:

| Model | WER | CER |
|---|---|---|
| Base (`<base>`) | … | … |
| Fine-tuned (`<checkpoint>`) | … | … |
| **Δ (improvement)** | … | … |

Note the split and sample count evaluated. If a run fails (missing checkpoint,
dataset auth), report the actual error and stop — do not fabricate numbers.
