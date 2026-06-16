#!/bin/bash

OUT_DIR=resources/dataset/twitteremo/genailabelled

LLM_ROUTER_MODEL="gpt-oss:120b"
LLM_ROUTER_HOST="http://192.168.100.65:8080"
DATASET_DIR="resources/dataset/twitteremo/"

mkdir -p "${OUT_DIR}"

genai-classifier \
  --dataset-dir="${DATASET_DIR}" \
  --prompts-dir=resources/prompts \
  --output-dir=${OUT_DIR} \
  --llm-router-url="${LLM_ROUTER_HOST}" \
  --model-name="${LLM_ROUTER_MODEL}" \
  --temperature=0.0 \
  --batch-save-size=2 \
  --num-workers=2 \
  --n-sample=0 \
  --text-column-name="tekst"

python3 code/dataset/convert_genai_to_training.py \
  --input "${OUT_DIR}/clarinpl-twitteremo-train-sample-5k_clean_labels.jsonl" \
  --output "${OUT_DIR}/clarinpl-twitteremo-train-sample-5k_training.jsonl"
