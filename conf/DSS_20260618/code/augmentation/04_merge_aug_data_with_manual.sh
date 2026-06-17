#!/bin/bash

DATA_DIR=resources/dataset/twitteremo

OUT_DIR_MERGED="${DATA_DIR}/merged"
OUT_DIR_AUGMENTED="${DATA_DIR}/augmented"

#LLM_ROUTER_MODEL="gpt-oss:120b"
#LLM_ROUTER_HOST="http://192.168.100.65:8080"

#DATASET_JSONL_FILE="${DATA_DIR}/clarinpl-twitteremo-train-sample-5k.jsonl"
#LABELED_DATASET_JSONL="${DATA_DIR}/clarinpl-twitteremo-train-sample-5k_labels.jsonl"
OUT_MERGED_PNG="${OUT_DIR_MERGED}/clarinpl-twitteremo-train-sample-5k-and-augmented-pos-1_7k.png"
OUT_MERGED_JSONL="${OUT_DIR_MERGED}/clarinpl-twitteremo-train-sample-5k-and-augmented-pos-1_7k.jsonl"

mkdir -p "${OUT_DIR_MERGED}"
mkdir -p "${OUT_DIR_AUGMENTED}"


# Dołączanie zbioru augmentowanego do ręcznego
cat \
  "${OUT_DIR_AUGMENTED}/clarinpl-twitteremo-train-sample-5k_labels_augmented-training.jsonl" \
  "${DATA_DIR}/clarinpl-twitteremo-train-sample-5k.jsonl" | sed 's/"text"/"tekst"/g' | sort | uniq > "${OUT_MERGED_JSONL}"

# Rozkład klas po łączeniu
python3 code/dataset/visualize_class_distribution.py \
  --train "${OUT_MERGED_JSONL}" \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --output "${OUT_MERGED_PNG}"