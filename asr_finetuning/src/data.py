"""Dataset loading, preprocessing, and the speech seq2seq data collator."""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Any

import librosa
import soundfile as sf
import torch
from datasets import Audio, DatasetDict, load_dataset

# Arabic punctuation + Latin punctuation we may strip when normalising text.
_PUNCT_RE = re.compile(r"[\.\,\;\:\!\?\"\'\(\)\[\]\{\}«»…ـ،؛؟]")


def _normalise_text(text: str, lowercase: bool, remove_punctuation: bool) -> str:
    text = text.strip()
    if remove_punctuation:
        text = _PUNCT_RE.sub("", text)
    if lowercase:
        text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def _require_columns(dataset, audio_column: str, text_column: str, name: str) -> None:
    """Fail early with a helpful message if expected columns are absent."""
    available = dataset.column_names
    missing = [c for c in (audio_column, text_column) if c not in available]
    if missing:
        raise ValueError(
            f"Dataset '{name}' is missing column(s) {missing}. "
            f"Available columns: {available}. "
            f"Set dataset.audio_column / dataset.text_column to match — e.g. "
            f"DODa uses audio='audio', text='darija_Arab_new' (Arabic script)."
        )


def _load_audio_array(audio: dict, target_sr: int):
    """Load a 1-D float waveform without datasets/torchcodec (works on Mac CPU)."""
    if audio.get("array") is not None:
        arr = audio["array"]
        sr = int(audio.get("sampling_rate") or target_sr)
    elif audio.get("bytes"):
        arr, sr = sf.read(io.BytesIO(audio["bytes"]), dtype="float32")
        if getattr(arr, "ndim", 1) > 1:
            arr = arr.mean(axis=1)
        sr = int(sr)
    elif audio.get("path"):
        arr, _ = librosa.load(audio["path"], sr=target_sr, mono=True)
        return arr, target_sr
    else:
        raise ValueError(f"Cannot load audio from keys {list(audio.keys())}")

    if sr != target_sr:
        arr = librosa.resample(arr, orig_sr=sr, target_sr=target_sr)
    return arr, target_sr


def _drop_empty_transcripts(dataset, text_column: str, name: str):
    """Remove rows with missing or blank transcripts (DODa has ~22 nulls)."""
    before = len(dataset)

    def keep(text) -> bool:
        return text is not None and str(text).strip() != ""

    filtered = dataset.filter(keep, input_columns=[text_column])
    dropped = before - len(filtered)
    if dropped:
        print(
            f"[data] Dropped {dropped} row(s) with empty '{text_column}' in {name}."
        )
    return filtered


def _grouped_split(dataset, group_column: str, test_size: float, seed: int):
    """Split rows so a value in `group_column` never appears in both halves.

    Parallel datasets like DODa record the same sentence multiple times; a plain
    random row split would leak those sentences across train/eval and inflate the
    score. We split the *unique* transcripts instead, then assign whole groups.
    """
    import random

    values = dataset[group_column]
    groups = sorted(set(values))
    random.Random(seed).shuffle(groups)
    n_eval = max(1, int(len(groups) * test_size))
    eval_groups = set(groups[:n_eval])
    eval_idx, train_idx = [], []
    for i, v in enumerate(values):
        (eval_idx if v in eval_groups else train_idx).append(i)
    return dataset.select(train_idx), dataset.select(eval_idx)


def load_splits(cfg: dict) -> DatasetDict:
    """Load train/eval splits from a Hugging Face dataset name in the config.

    Robust to real-world Darija sets: if the eval split is missing (or
    `dataset.eval_split` is null) a validation set is carved out of train using
    `dataset.test_size`, split by sentence so no transcript appears in both
    train and eval. Missing columns raise a clear, actionable error.
    """
    d = cfg["dataset"]
    load_kwargs: dict[str, Any] = {}
    if d.get("config"):
        load_kwargs["name"] = d["config"]

    raw = DatasetDict()
    raw["train"] = load_dataset(d["name"], split=d["train_split"], **load_kwargs)
    raw["train"] = _drop_empty_transcripts(raw["train"], d["text_column"], d["name"])

    eval_split = d.get("eval_split")
    if eval_split:
        try:
            raw["eval"] = load_dataset(d["name"], split=eval_split, **load_kwargs)
            raw["eval"] = _drop_empty_transcripts(
                raw["eval"], d["text_column"], d["name"]
            )
        except (ValueError, KeyError):
            print(
                f"[data] eval split '{eval_split}' not found in {d['name']}; "
                f"carving {d.get('test_size', 0.1):.0%} of train for validation."
            )
            eval_split = None
    if not eval_split:
        # Validate before carving: the grouped split needs the text column.
        _require_columns(raw["train"], d["audio_column"], d["text_column"], d["name"])
        raw["train"], raw["eval"] = _grouped_split(
            raw["train"],
            d["text_column"],
            test_size=float(d.get("test_size", 0.1)),
            seed=cfg["training"]["seed"],
        )

    # Validate + normalise columns to canonical {audio, text}.
    for split in raw:
        _require_columns(raw[split], d["audio_column"], d["text_column"], d["name"])
        rename = {}
        if d["audio_column"] != "audio":
            rename[d["audio_column"]] = "audio"
        if d["text_column"] != "text":
            rename[d["text_column"]] = "text"
        if rename:
            raw[split] = raw[split].rename_columns(rename)
        drop = [c for c in raw[split].column_names if c not in {"audio", "text"}]
        raw[split] = raw[split].remove_columns(drop)

    # Optional sub-sampling for quick smoke tests.
    if d.get("max_train_samples"):
        raw["train"] = raw["train"].select(range(int(d["max_train_samples"])))
    if d.get("max_eval_samples"):
        raw["eval"] = raw["eval"].select(range(int(d["max_eval_samples"])))

    sr = cfg["preprocessing"]["sampling_rate"]
    # decode=False avoids torchcodec/FFmpeg; bytes are loaded in prepare() via soundfile.
    raw = raw.cast_column("audio", Audio(sampling_rate=sr, decode=False))
    return raw


def build_prepare_fn(cfg: dict, feature_extractor, tokenizer):
    """Return a map() function turning raw rows into model inputs + labels."""
    pre = cfg["preprocessing"]
    max_audio_samples = int(pre["max_audio_seconds"] * pre["sampling_rate"])

    def prepare(batch: dict) -> dict:
        audio = batch["audio"]
        array, sampling_rate = _load_audio_array(audio, pre["sampling_rate"])
        features = feature_extractor(array, sampling_rate=sampling_rate)
        batch["input_features"] = features.input_features[0]
        batch["input_length"] = len(array)

        text = _normalise_text(
            batch["text"], pre["lowercase"], pre["remove_punctuation"]
        )
        batch["labels"] = tokenizer(text).input_ids
        return batch

    return prepare, max_audio_samples


@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Pads input features and label sequences independently."""

    processor: Any
    decoder_start_token_id: int

    def __call__(self, features: list[dict]) -> dict[str, torch.Tensor]:
        input_features = [{"input_features": f["input_features"]} for f in features]
        batch = self.processor.feature_extractor.pad(
            input_features, return_tensors="pt"
        )

        label_features = [{"input_ids": f["labels"]} for f in features]
        labels_batch = self.processor.tokenizer.pad(
            label_features, return_tensors="pt"
        )
        # Replace padding with -100 so it is ignored by the loss.
        labels = labels_batch["input_ids"].masked_fill(
            labels_batch.attention_mask.ne(1), -100
        )
        # If a BOS token was appended in tokenisation, strip it; the model adds it.
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels
        return batch
