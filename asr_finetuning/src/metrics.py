"""WER / CER metric computation for the Seq2SeqTrainer."""
from __future__ import annotations

import evaluate

_wer = evaluate.load("wer")
_cer = evaluate.load("cer")


def build_compute_metrics(tokenizer):
    """Return a compute_metrics(pred) closure for the Trainer."""

    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids

        # -100 was used to pad labels; restore the real pad token before decoding.
        label_ids[label_ids == -100] = tokenizer.pad_token_id

        pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

        wer = 100 * _wer.compute(predictions=pred_str, references=label_str)
        cer = 100 * _cer.compute(predictions=pred_str, references=label_str)
        return {"wer": wer, "cer": cer}

    return compute_metrics
