#!/usr/bin/env bash
# Tiny end-to-end run to verify the pipeline works before a full training job.
# Uses a handful of samples and very few steps. Requires a dataset you can access.
set -euo pipefail
cd "$(dirname "$0")/.."

# Use DODa (doda_darija.yaml): it's the primary Darija set and loads on any
# datasets version. (The CV17 default needs datasets<4, pinned in requirements.txt.)
python -m src.train \
  --config config/doda_darija.yaml \
  --dataset.max_train_samples 32 \
  --dataset.max_eval_samples 16 \
  --training.max_steps 5 \
  --training.eval_steps 5 \
  --training.save_steps 5 \
  --training.warmup_steps 1 \
  --training.per_device_train_batch_size 4 \
  --training.per_device_eval_batch_size 4 \
  --training.fp16 false \
  --training.output_dir ./outputs/smoke
