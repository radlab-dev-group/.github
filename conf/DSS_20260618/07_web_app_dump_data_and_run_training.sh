 #!/bin/bash

export PYTHONPATH=$PYTHONPATH:.

# Tworzymy zrzut danych z bazy decyzji usderów (nieoznaczone też wpadają do datasetu)
# Uczymy model na zmergowanym datasecie

# 1. Zrzut danych z bazy danych
python3 code/dataset/dump_dataset_from_web_app.py \
  --model "/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented" \
  --output-path "resources/dataset/twitteremo/active_learning/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning.jsonl"

# 2. Uruchomienie treningu (miejsce na wywołanie skryptu trenującego)
# Model wyuczony jest pod ściezką /mnt/local....
# i dostępny będzie w aplikacji
#  -> Podgląd na Confusion Matrix w wandb
