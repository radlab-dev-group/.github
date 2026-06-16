# 1. dataset — download_and_prepare_sample_twitteremo

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

---

# 2. dataset — visualize_class_distribution

Wizualizuje rozkład klas `negatywny`, `pozytywny` i `neutralny`
w plikach JSONL (train / valid) jako wykres słupkowy PNG.

## Instalacja

```bash
pip install matplotlib
```

## Użycie z wiersza poleceń

```bash
# Domyślne pliki wejściowe
python3 resources/dataset/visualize_class_distribution.py

# Własne ścieżki
python3 code/dataset/visualize_class_distribution.py \
  --train resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --output resources/dataset/twitteremo/clarinpl-twitteremo-train-valide-distribution.png
```

## Parametry

| Parametr   | Domyślna wartość                                                          | Opis                         |
|------------|---------------------------------------------------------------------------|------------------------------|
| `--train`  | `resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl`  | Ścieżka do pliku train JSONL |
| `--valid`  | `resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl` | Ścieżka do pliku valid JSONL |
| `--output` | `resources/dataset/twitteremo/class_distribution.png`                     | Ścieżka wyjściowa obrazu PNG |
