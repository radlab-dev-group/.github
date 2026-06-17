#!/bin/bash

OUT_DIR="/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented"

rm -rf "${OUT_DIR}"

# Uczymy model na danych ręczne + augmentowane
#  -> Oceniamy go na wydzielonym niezależnie samplu 500 przykładów
#  -> Ocena tego modelu i modelu uczonego na podstawie ręcznych anotacji jest na tym samym valid-set

CUDA_VISIBLE_DEVICES=1 python3 code/training/train_polarity_model.py \
  --train resources/dataset/twitteremo/merged/clarinpl-twitteremo-train-sample-5k-and-augmented-pos-1_7k.jsonl \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --base-model-path allegro/herbert-base-cased \
  --num-epochs 5 \
  --batch-size 32 \
  --learning-rate 3e-6 \
  --wandb-project polar-twitteremo \
  --output-dir "${OUT_DIR}"
