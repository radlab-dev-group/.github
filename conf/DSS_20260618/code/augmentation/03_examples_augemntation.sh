#!/bin/bash

OUT_DIR=resources/dataset/twitteremo/augmented

LLM_ROUTER_MODEL="gpt-oss:120b"
LLM_ROUTER_HOST="http://192.168.100.65:8080"

DATASET_JSONL_FILE="resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl"
LABELED_DATASET_JSONL="resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k_labels.jsonl"

mkdir -p "${OUT_DIR}"

python3 code/dataset/convert_raw_clarin_to_labels.py \
  --input "${DATASET_JSONL_FILE}" \
  --output "${LABELED_DATASET_JSONL}"

genai-data-augmentation \
  --dataset-path="${LABELED_DATASET_JSONL}" \
  --labels="pozytywny" \
  --output-dir="${OUT_DIR}" \
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

python3 code/dataset/convert_genai_to_training.py \
  --input "${OUT_DIR}/clarinpl-twitteremo-train-sample-5k_labels_augmented-train.jsonl" \
  --output "${OUT_DIR}/clarinpl-twitteremo-train-sample-5k_labels_augmented-training.jsonl"
