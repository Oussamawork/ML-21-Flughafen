"""Fine-tune Whisper for Darija/Arabic ASR.

Usage:
    python -m src.train --config config/default.yaml
    python -m src.train --config config/default.yaml --training.max_steps 1000

Run from the asr_finetuning/ directory.
"""
from __future__ import annotations

import os

from transformers import (
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    WhisperFeatureExtractor,
    WhisperForConditionalGeneration,
    WhisperProcessor,
    WhisperTokenizer,
)

from .config import load_config
from .data import (
    DataCollatorSpeechSeq2SeqWithPadding,
    build_prepare_fn,
    load_splits,
)
from .metrics import build_compute_metrics


def main() -> None:
    cfg = load_config()
    m, t = cfg["model"], cfg["training"]

    print(f"Loading base model: {m['name']} (language={m['language']}, task={m['task']})")
    feature_extractor = WhisperFeatureExtractor.from_pretrained(m["name"])
    tokenizer = WhisperTokenizer.from_pretrained(
        m["name"], language=m["language"], task=m["task"]
    )
    processor = WhisperProcessor.from_pretrained(
        m["name"], language=m["language"], task=m["task"]
    )
    model = WhisperForConditionalGeneration.from_pretrained(m["name"])

    # Let the model freely predict the language/task during generation instead of
    # forcing legacy decoder prompt ids; set the generation language explicitly.
    model.generation_config.language = m["language"]
    model.generation_config.task = m["task"]
    model.generation_config.forced_decoder_ids = None
    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []
    if t.get("gradient_checkpointing"):
        model.config.use_cache = False

    print("Loading and preprocessing dataset...")
    ds = load_splits(cfg)
    prepare, max_audio_samples = build_prepare_fn(cfg, feature_extractor, tokenizer)
    ds = ds.map(
        prepare,
        remove_columns=ds["train"].column_names,
        num_proc=t.get("num_workers", 1),
        desc="extract features",
    )

    # Filter out clips that are too long (bounds memory / training time).
    def _ok(input_length: int) -> bool:
        return input_length <= max_audio_samples

    ds["train"] = ds["train"].filter(_ok, input_columns=["input_length"])

    collator = DataCollatorSpeechSeq2SeqWithPadding(
        processor=processor,
        decoder_start_token_id=model.config.decoder_start_token_id,
    )
    compute_metrics = build_compute_metrics(tokenizer)

    args = Seq2SeqTrainingArguments(
        output_dir=t["output_dir"],
        per_device_train_batch_size=t["per_device_train_batch_size"],
        per_device_eval_batch_size=t["per_device_eval_batch_size"],
        gradient_accumulation_steps=t["gradient_accumulation_steps"],
        learning_rate=float(t["learning_rate"]),
        warmup_steps=t["warmup_steps"],
        max_steps=t["max_steps"],
        gradient_checkpointing=t["gradient_checkpointing"],
        fp16=t["fp16"],
        eval_strategy=t["eval_strategy"],
        eval_steps=t["eval_steps"],
        save_steps=t["save_steps"],
        logging_steps=t["logging_steps"],
        save_total_limit=t["save_total_limit"],
        predict_with_generate=t["predict_with_generate"],
        generation_max_length=t["generation_max_length"],
        load_best_model_at_end=t["load_best_model_at_end"],
        metric_for_best_model=t["metric_for_best_model"],
        greater_is_better=t["greater_is_better"],
        report_to=[t["report_to"]] if t.get("report_to") else [],
        seed=t["seed"],
        push_to_hub=t["push_to_hub"],
        hub_model_id=t.get("hub_model_id"),
        dataloader_num_workers=t.get("num_workers", 0),
        remove_unused_columns=False,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=ds["train"],
        eval_dataset=ds["eval"],
        data_collator=collator,
        compute_metrics=compute_metrics,
        processing_class=processor,
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving best model + processor to {t['output_dir']}")
    trainer.save_model(t["output_dir"])
    processor.save_pretrained(t["output_dir"])

    metrics = trainer.evaluate()
    print("Final eval metrics:", metrics)
    with open(os.path.join(t["output_dir"], "final_metrics.txt"), "w") as f:
        for k, v in metrics.items():
            f.write(f"{k}: {v}\n")

    if t.get("push_to_hub"):
        trainer.push_to_hub()


if __name__ == "__main__":
    main()
