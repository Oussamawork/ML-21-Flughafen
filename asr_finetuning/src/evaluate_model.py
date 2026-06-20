"""Evaluate a fine-tuned (or base) Whisper checkpoint on a dataset split.

Usage:
    python -m src.evaluate_model --config config/default.yaml \
        --model.name ./outputs/whisper-small-darija
"""
from __future__ import annotations

import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

from .config import load_config
from .data import build_prepare_fn, load_splits
from .metrics import _cer, _wer


def main() -> None:
    cfg = load_config()
    m = cfg["model"]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    processor = WhisperProcessor.from_pretrained(
        m["name"], language=m["language"], task=m["task"]
    )
    model = WhisperForConditionalGeneration.from_pretrained(m["name"]).to(device)
    model.eval()

    ds = load_splits(cfg)
    prepare, _ = build_prepare_fn(
        cfg, processor.feature_extractor, processor.tokenizer
    )
    eval_ds = ds["eval"].map(
        prepare, remove_columns=ds["eval"].column_names, desc="prepare eval"
    )

    batch_size = cfg["training"]["per_device_eval_batch_size"]
    preds: list[str] = []
    refs: list[str] = []

    for start in range(0, len(eval_ds), batch_size):
        rows = eval_ds[start : start + batch_size]
        feats = processor.feature_extractor.pad(
            [{"input_features": f} for f in rows["input_features"]],
            return_tensors="pt",
        ).input_features.to(device)

        with torch.no_grad():
            generated = model.generate(feats, max_length=225)
        preds.extend(processor.batch_decode(generated, skip_special_tokens=True))

        label_ids = [
            [tok for tok in seq if tok != -100] for seq in rows["labels"]
        ]
        refs.extend(processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True))

    wer = 100 * _wer.compute(predictions=preds, references=refs)
    cer = 100 * _cer.compute(predictions=preds, references=refs)
    print(f"Samples: {len(refs)}")
    print(f"WER: {wer:.2f}%")
    print(f"CER: {cer:.2f}%")
    for ref, pred in zip(refs[:5], preds[:5]):
        print(f"\n  REF : {ref}\n  PRED: {pred}")


if __name__ == "__main__":
    main()
