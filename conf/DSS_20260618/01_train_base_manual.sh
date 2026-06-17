#!/bin/bash

OUT_DIR="/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual"

rm -rf "${OUT_DIR}"

CUDA_VISIBLE_DEVICES=1 python3 code/training/train_polarity_model.py \
  --train resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --base-model-path allegro/herbert-base-cased \
  --num-epochs 5 \
  --batch-size 32 \
  --learning-rate 3e-6 \
  --wandb-project polar-twitteremo \
  --output-dir "${OUT_DIR}"
