#!/bin/bash

python3 code/dataset/visualize_class_distribution.py \
  --train resources/dataset/twitteremo/genailabelled/clarinpl-twitteremo-train-sample-5k_training.jsonl \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --output resources/dataset/twitteremo/genailabelled/clarinpl-twitteremo-train-valid-distribution.png