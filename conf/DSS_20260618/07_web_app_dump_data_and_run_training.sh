 #!/bin/bash

export PYTHONPATH=$PYTHONPATH:.

DATA_DIR="resources/dataset/twitteremo"

OUT_WEB_FILE_DUMP="${DATA_DIR}/active_learning/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning.jsonl"
OUT_WEB_FILE_DUMP_DISTR="${DATA_DIR}/active_learning/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning.png"

OUT_TRAINING_FILE="${DATA_DIR}/active_learning/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning-training.jsonl"
OUT_TRAINING_FILE_DISTR="${DATA_DIR}/active_learning/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning-training.png"

OUT_AL_MODEL_DIR="/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning"

# ----------------------------------------------------------------------------------------------------------------------
# 1. Zrzut danych z bazy danych
# Tworzymy zrzut danych z bazy decyzji usderów (nieoznaczone też wpadają do datasetu)
python3 code/dataset/dump_dataset_from_web_app.py \
  --model "/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented" \
  --output-path "${OUT_WEB_FILE_DUMP}"

# ----------------------------------------------------------------------------------------------------------------------
# 2. Łączymy oba datasety w jeden i przygotowujemy rozkład klas
# rozkład tylko AL (dump z bazy app-web)
python3 code/dataset/visualize_class_distribution.py \
  --train "${OUT_WEB_FILE_DUMP}" \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --output "${OUT_WEB_FILE_DUMP_DISTR}"

# łączymy zbiory
cat \
  "${OUT_WEB_FILE_DUMP}" \
  "${DATA_DIR}/clarinpl-twitteremo-train-sample-5k.jsonl" | \
  sed 's/"text"/"tekst"/g' | sort | uniq > \
  "${OUT_TRAINING_FILE}"

# Rozkład dla smergowanego datasetu
python3 code/dataset/visualize_class_distribution.py \
  --train "${OUT_TRAINING_FILE}" \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --output "${OUT_TRAINING_FILE_DISTR}"


# ----------------------------------------------------------------------------------------------------------------------
# 3. Uruchomienie treningu (miejsce na wywołanie skryptu trenującego)
# Uczymy model na danych ręczne + augmentowane + po activle learning (HIL)
#  -> Oceniamy go na wydzielonym niezależnie samplu 500 przykładów
#  -> Ocena tego modelu jest na tym samym valid-set co w pozostałych treningach
rm -rf "${OUT_AL_MODEL_DIR}"

CUDA_VISIBLE_DEVICES=1 python3 code/training/train_polarity_model.py \
  --train "${OUT_TRAINING_FILE}" \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --base-model-path allegro/herbert-base-cased \
  --num-epochs 5 \
  --batch-size 32 \
  --learning-rate 3e-6 \
  --wandb-project polar-twitteremo \
  --output-dir "${OUT_AL_MODEL_DIR}"
