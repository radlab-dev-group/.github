# dataset — download_and_prepare_sample_twitteremo

Pobiera losowy podzbiór przykładów z datasetu `clarin-pl/twitteremo`
na HuggingFace Hub i zapisuje je do pliku JSONL.

## Instalacja

```bash
pip install datasets
```

## Użycie z wiersza poleceń

```bash
# Domyślne wartości (clarin-pl/twitteremo, split=train, 100 próbek)
python3 dataset/download_and_prepare_sample.py

# Tylko train
python3 dataset/download_and_prepare_sample.py \
    --dataset clarin-pl/twitteremo \
    --split train \
    --num-samples 5000 \
    --output train.jsonl \
    --seed 42

# Train + valid (zbiór rozłączny od train)
python3 dataset/download_and_prepare_sample.py \
    --dataset clarin-pl/twitteremo \
    --split train \
    --num-samples 5000 \
    --num-samples-valid 1000 \
    --output train.jsonl \
    --output-valid valid.jsonl \
    --seed 42
```

## Parametry

| Parametr              | Domyślna wartość       | Opis                                                     |
|-----------------------|------------------------|----------------------------------------------------------|
| `--dataset`           | `clarin-pl/twitteremo` | Nazwa datasetu HF                                        |
| `--split`             | `train`                | Nazwa splitu                                             |
| `--num-samples`       | `100`                  | Liczba losowych przykładów do train                      |
| `--output`            | `samples.jsonl`        | Ścieżka pliku wyjściowego (train)                        |
| `--num-samples-valid` | `0`                    | Liczba losowych przykładów do valid (rozłączny od train) |
| `--output-valid`      | `samples_valid.jsonl`  | Ścieżka pliku wyjściowego (valid)                        |
| `--seed`              | `None`                 | Seed dla reproducowalności                               |
