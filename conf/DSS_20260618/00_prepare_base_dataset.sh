#!/bin/bash

# Przygotowanie datasetu do modelu bazowego
python3 code/dataset/download_and_prepare_sample_twitteremo.py \
    --dataset clarin-pl/twitteremo \
    --split train \
    --num-samples 5000 \
    --num-samples-valid 500 \
    --output resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \
    --output-valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
    --seed 42