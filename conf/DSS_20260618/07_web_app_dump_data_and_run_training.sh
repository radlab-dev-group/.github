 #!/bin/bash

export PYTHONPATH=$PYTHONPATH:.

OUT_TRAINING_FILE="resources/dataset/twitteremo/active_learning/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning.jsonl"
OUT_TRAINING_FILE_DISTR="resources/dataset/twitteremo/active_learning/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning.png"

# ----------------------------------------------------------------------------------------------------------------------
# 1. Zrzut danych z bazy danych
# Tworzymy zrzut danych z bazy decyzji usderów (nieoznaczone też wpadają do datasetu)
python3 code/dataset/dump_dataset_from_web_app.py \
  --model "/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented" \
  --output-path "${OUT_TRAINING_FILE}"

# ----------------------------------------------------------------------------------------------------------------------
# 2. Przygotowujemy rozkład klas
python3 code/dataset/visualize_class_distribution.py \
  --train "${OUT_TRAINING_FILE}" \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --output "${OUT_TRAINING_FILE_DISTR}"

# ----------------------------------------------------------------------------------------------------------------------
# 3. Uruchomienie treningu (miejsce na wywołanie skryptu trenującego)
# Uczymy model na danych ręczne + augmentowane + po activle learning (HIL)
#  -> Oceniamy go na wydzielonym niezależnie samplu 500 przykładów
#  -> Ocena tego modelu jest na tym samym valid-set co w pozostałych treningach

OUT_DIR="/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning"
rm -rf "${OUT_DIR}"
CUDA_VISIBLE_DEVICES=1 python3 code/training/train_polarity_model.py \
  --train "${OUT_TRAINING_FILE}" \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --base-model-path allegro/herbert-base-cased \
  --num-epochs 5 \
  --batch-size 32 \
  --learning-rate 3e-6 \
  --wandb-project polar-twitteremo \
  --output-dir "${OUT_DIR}"
