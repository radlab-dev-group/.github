# 1. code/dataset/download_and_prepare_sample_twitteremo

Pobiera losowy podzbiór przykładów z datasetu `clarin-pl/twitteremo`
na [HuggingFace Hub](https://huggingface.co/datasets/clarin-pl/twitteremo) i zapisuje je do pliku JSONL.
Obsługa zbiorów train i valid (rozłącznych od siebie).

## Instalacja

```bash
pip install datasets
```

## Użycie z wiersza poleceń

```bash
# Tylko train
python3 code/dataset/download_and_prepare_sample_twitteremo.py \
    --dataset clarin-pl/twitteremo \
    --split train \
    --num-samples 5000 \
    --output resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \
    --seed 42

# Train + valid (zbiór rozłączny od train)
python3 code/dataset/download_and_prepare_sample_twitteremo.py \
    --dataset clarin-pl/twitteremo \
    --split train \
    --num-samples 5000 \
    --num-samples-valid 500 \
    --output resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \
    --output-valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
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

# 2. code/dataset/visualize_class_distribution

Wizualizuje rozkład klas `negatywny`, `pozytywny` i `neutralny`
w plikach JSONL (train / valid) jako wykres słupkowy PNG.

## Instalacja

```bash
pip install matplotlib
```

## Użycie z wiersza poleceń

```bash
# Własne ścieżki
python3 code/dataset/visualize_class_distribution.py \
  --train resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --output resources/dataset/twitteremo/class_distribution.png
```

## Parametry

| Parametr   | Domyślna wartość                                                          | Opis                         |
|------------|---------------------------------------------------------------------------|------------------------------|
| `--train`  | `resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl`  | Ścieżka do pliku train JSONL |
| `--valid`  | `resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl` | Ścieżka do pliku valid JSONL |
| `--output` | `resources/dataset/twitteremo/class_distribution.png`                     | Ścieżka wyjściowa obrazu PNG |

---

# 3. code/dataset/convert_raw_clarin_to_labels

Konwertuje surowy dataset Clarin PL TwitterEmo (z wieloma polami emocji)
na format z kluczem `text` i listą `labels` (przydatne przed augmentacją).

## Użycie z wiersza poleceń

```bash
python3 code/dataset/convert_raw_clarin_to_labels.py \
    --input resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \
    --output resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k_labels.jsonl
```

## Parametry

| Parametr   | Opis                                           |
|------------|------------------------------------------------|
| `--input`  | Ścieżka do surowego pliku wejściowego          |
| `--output` | Ścieżka wyjściowa (domyślnie `<input>_labels`) |

---

# 4. code/dataset/convert_genai_to_training

Konwertuje dane wyjściowe z `genai-classifier` na format akceptowany przez aplikację do treningu modelu.
Mapuje etykiety tekstowe (Pozytywna, Negatywna, Neutralna) na kolumny binarne oraz zapewnia
obecność wymaganych pól (np. emocje) z domyślnymi wartościami.

## Użycie z wiersza poleceń

```bash
python3 code/dataset/convert_genai_to_training.py \
    --input resources/dataset/twitteremo/genailabelled/clarinpl-twitteremo-train-sample-5k_clean_labels.jsonl \
    --output resources/dataset/twitteremo/genailabelled/clarinpl-twitteremo-train-sample-5k_training.jsonl
```

## Parametry

| Parametr   | Opis                         |
|------------|------------------------------|
| `--input`  | Ścieżka do pliku wejściowego |
| `--output` | Ścieżka do pliku wyjściowego |

---

# 5. code/training/train_polarity_model

Trenuje klasyfikator polaryzacji tekstu (pozytywny / negatywny / neutralny)
na próbkach z twitteremo przy użyciu modelu bazowego (domyślnie `allegro/herbert-base-cased`)
oraz loguje metryki do Weights & Biases.

## Instalacja

```bash
pip install torch transformers wandb scikit-learn
```

## Użycie z wiersza poleceń

```bash
# Domyślne parametry
python3 code/training/train_polarity_model.py

# Pełna konfiguracja
python3 code/training/train_polarity_model.py \
    --train resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \
    --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
    --base-model-path allegro/herbert-base-cased \
    --num-epochs 5 \
    --batch-size 32 \
    --learning-rate 1e-5 \
    --max-length 128 \
    --wandb-project polar-twitteremo \
    --wandb-entity radlab \
    --output-dir output/polarity-model/twitter-emo-sample-5k
```

## Parametry

| Parametr            | Domyślna wartość                                                          | Opis                                 |
|---------------------|---------------------------------------------------------------------------|--------------------------------------|
| `--train`           | `resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl`  | Ścieżka do pliku train JSONL         |
| `--valid`           | `resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl` | Ścieżka do pliku valid JSONL         |
| `--base-model-path` | `allegro/herbert-base-cased`                                              | Nazwa lub ścieżka do modelu bazowego |
| `--num-epochs`      | `5`                                                                       | Liczba epok treningu                 |
| `--batch-size`      | `32`                                                                      | Rozmiar batcha                       |
| `--learning-rate`   | `1e-5`                                                                    | Learning rate                        |
| `--max-length`      | `128`                                                                     | Max długość sekwencji                |
| `--wandb-project`   | `polar-twitteremo`                                                        | Nazwa projektu W&B                   |
| `--wandb-entity`    | `None`                                                                    | Entitet / team W&B                   |
| `--output-dir`      | `output/polarity-model`                                                   | Katalog zapisu modelu                |

---

# 6. code/augmentation/ — Skrypty augmentacji

## 6.1 `01_label_with_genai.sh` — Anotacja przez genai-classifier

Uruchamia `genai-classifier` z LLM `gpt-oss:120b` w celu automatycznej
klasyfikacji polaryzacji (Pozytywna / Negatywna / Neutralna) oraz konwersji
do formatu treningowego.

```bash
bash code/augmentation/01_label_with_genai.sh
```

## 6.2 `02_select_class_to_augmentation.sh` — Wizualizacja przed augmentacją

Generuje wykres rozkładu klas po annotacji, w celu weryfikacji
równowagi przed generowaniem augmentacji.

```bash
bash code/augmentation/02_select_class_to_augmentation.sh
```

## 6.3 `03_examples_augemntation.sh` — Generowanie + merge + wizualizacja

Główny skrypt pipeline'a augmentacji:

1. **Konwersja** surowego datasetu do formatu `text` + `labels`.
2. **Augmentacja** przez `genai-data-augmentation` (LLM `gpt-oss:120b`, ~350 przykładów na klasę).
3. **Konwersja** wyniku do formatu treningowego.
4. **Merge** z originalnym datasetem (~5k + ~1.7k).
5. **Wizualizacja** rozkładu klas po połączeniu.

```bash
bash code/augmentation/03_examples_augemntation.sh
```

**Parametry augmentacji:**

- `--n-sample 350` — liczba przykładów na klasę
- `--n-examples 5` — liczba przykładów wygenerowanych na jeden podany do LLM
- `--samples-as-examples 2` — liczba samples jako in-context examples
- `--temperature 0.0` — deterministyczna augmentacja
- `--labels pozytywny` — klasa docelowa do augmentacji

---

# 7. code/web_app

Aplikacja webowa (Flask) do wizualnej oceny działania modelu polaryzacji oraz ręcznej anotacji danych.
Pozwala na porównanie predykcji modelu z opinią użytkownika i zapisywanie wyników w bazie SQLite.

## Funkcje

- Losowanie przykładów z bazy danych.
- Automatyczna predykcja wybranym modelem (Transformers).
- Interfejs do zapisywania ocen użytkownika.

## Instalacja i uruchomienie

Wymagany Python 3.10+.

```bash
# Uruchomienie aplikacji (z bazy SQLite)
bash code/web_app/run_app.sh
# Aplikacja jest dostępna pod http://localhost:5000

# Import danych do bazy
bash code/web_app/import_to_db.sh resources/dataset/twitteremo/augmented/clarinpl-twitteremo-train-sample-5k_labels_augmented-training.jsonl
```

## Struktura plików aplikacji

- `app.py`: Główny serwer Flask, logika predykcji, import modeli.
- `models.py`: Definicje tabel bazy danych (SQLAlchemy) — `Example`, `Annotation`.
- `import_data.py`: Skrypt do zasilania bazy danych z plików JSONL.
- `import_to_db.sh`: Obudowka shell do importu danych.
- `templates/index.html`: Interfejs użytkownika (Bootstrap + JS).
