#!/bin/bash

DATA_DIR=resources/dataset/twitteremo

OUT_DIR_MERGED="${DATA_DIR}/merged"
OUT_DIR_AUGMENTED="${DATA_DIR}/augmented"

LLM_ROUTER_MODEL="gpt-oss:120b"
LLM_ROUTER_HOST="http://192.168.100.65:8080"

DATASET_JSONL_FILE="${DATA_DIR}/clarinpl-twitteremo-train-sample-5k.jsonl"
LABELED_DATASET_JSONL="${DATA_DIR}/clarinpl-twitteremo-train-sample-5k_labels.jsonl"
OUT_MERGED_PNG="${OUT_DIR_MERGED}/clarinpl-twitteremo-train-sample-5k-and-augmented-pos-1_7k.png"
OUT_MERGED_JSONL="${OUT_DIR_MERGED}/clarinpl-twitteremo-train-sample-5k-and-augmented-pos-1_7k.jsonl"

mkdir -p "${OUT_DIR_MERGED}"
mkdir -p "${OUT_DIR_AUGMENTED}"

# Konwersja do formatu akceptowalnego przez genai-data-augmentation
python3 code/dataset/convert_raw_clarin_to_labels.py \
  --input "${DATASET_JSONL_FILE}" \
  --output "${LABELED_DATASET_JSONL}"

# Urchomienie genai-data-augmentation
genai-data-augmentation \
  --dataset-path="${LABELED_DATASET_JSONL}" \
  --labels="pozytywny" \
  --output-dir="${OUT_DIR_AUGMENTED}" \
  --prompt-file=resources/prompts/augomentator/augmentator.prompt \
  --labels=pozytywny \
  --llm-router-url="${LLM_ROUTER_HOST}" \
  --model-name="${LLM_ROUTER_MODEL}" \
  --temperature=0.0 \
  --batch-save-size=2 \
  --num-workers=2 \
  --n-sample=350 \
  --n-examples=5 \
  --samples-as-examples=2 \
  --text-column-name="text" \
  --label-column-name="labels"

# Konwersja genai-data-augmentation do formatu takiego samego
# jak clarinpl-twitteremo-train-sample-5k.jsonl -> aby wykorzystać ten sam skrypt uczący
python3 code/dataset/convert_genai_to_training.py \
  --input "${OUT_DIR_AUGMENTED}/clarinpl-twitteremo-train-sample-5k_labels_augmented-train.jsonl" \
  --output "${OUT_DIR_AUGMENTED}/clarinpl-twitteremo-train-sample-5k_labels_augmented-training.jsonl"
