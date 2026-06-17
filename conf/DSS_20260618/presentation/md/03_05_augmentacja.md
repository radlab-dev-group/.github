# Automatyczna augmentacja za pomocą utilsów

Powrót do [agendy](00_agenda.md).

---

`genai-data-augmentation` to CLI z pakietu **[llm-router-utils](https://github.com/radlab-dev-group/llm-router-utils)**, 
służący do generowania nowych przykładów treningowych na bazie istniejących danych. Działa w następujący sposób:

1. Pobiera zbiór danych z etykietami (JSONL) i wybiera przykłady z wybranej klasy.
2. Dla wybranych przykładów wysyła prompt augmentacyjny do LLM (przez llm-router).
3. LLM generuje nowe, zaugmentowane wersje tekstów zachowujące oryginalną etykietę.
4. Wyniki są zapisywane do pliku JSONL z dodatkowym polem `augment` (nowe przykłady).

```
┌──────────────────────────┐
│   dane wejściowe         │
│   (JSONL, z labels)      │
│   → selekcja klasy       │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│   genai-data-augmentation│
│                          │
│  dla każdego przykładu:  │
│  1. buduje prompt        │
│     augmentacyjny        │
│  2. wysyła do LLM        │
│  3. parsuje result       │
│                          │
│  • batch processing      │
│  • wielowątkowość        │
│  • retry on error        │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│   dane wyjściowe         │
│   (JSONL, z augmented)   │
└──────────────────────────┘
```

---

## Instalacja (z pakietu llm-router-utils)
```bash
git clone https://github.com/radlab-dev-group/llm-router-utils.git
cd llm-router-utils
pip install -e .
pip install ".[llm-router]"   # llm-router + llm-router-services z git
```

Po instalacji `genai-data-augmentation` jest dostępny jako komenda CLI.
Pełna lista parametrów:

```shell
genai-data-augmentation --help
usage: genai-data-augmentation [-h] --dataset-path DATASET_PATH --prompt-file PROMPT_FILE --labels LABELS [--n-samples N_SAMPLES] [--n-examples N_EXAMPLES] [--samples-as-examples SAMPLES_AS_EXAMPLES] [--llm-router-url LLM_ROUTER_URL] [--model-name MODEL_NAME] [--temperature TEMPERATURE]
                               [--batch-save-size BATCH_SAVE_SIZE] [--dry-run] [--output-dir OUTPUT_DIR] [--verbose] [--num-workers NUM_WORKERS] [--text-column-name TEXT_COLUMN_NAME] [--label-column-name LABEL_COLUMN_NAME] [--export-xlsx] [--no-export-xlsx]

Augment datasets using LLMRouter.

options:
  -h, --help            show this help message and exit
  --dataset-path DATASET_PATH
                        Path to the dataset file (XLSX or JSONL).
  --prompt-file PROMPT_FILE
                        Path to the prompt file.
  --labels LABELS       Comma-separated list of labels to augment.
  --n-samples N_SAMPLES
                        Number of random samples per class as examples to augment (use 0 for all).
  --n-examples N_EXAMPLES
                        Number of augmented examples the LLM should generate for each input text.
  --samples-as-examples SAMPLES_AS_EXAMPLES
                        Number of random samples per class from the dataset to include in the prompt context.
  --llm-router-url LLM_ROUTER_URL
                        Base URL of the LLMRouter service.
  --model-name MODEL_NAME
                        Model identifier passed to the router.
  --temperature TEMPERATURE
                        Sampling temperature for the model.
  --batch-save-size BATCH_SAVE_SIZE
                        How many records are written to disk at once.
  --dry-run             Process data but do not write output files.
  --output-dir OUTPUT_DIR
                        Override directory where result files are stored.
  --verbose             Enable DEBUG level logging.
  --num-workers NUM_WORKERS
                        Number of parallel worker threads.
  --text-column-name TEXT_COLUMN_NAME
                        Name of the column containing the text (default: 'Tekst').
  --label-column-name LABEL_COLUMN_NAME
                        Name of the column containing the label (default: 'label').
  --export-xlsx         Convert output JSONL files to XLSX format (default: True).
  --no-export-xlsx      Disable XLSX export.   
```

---

## Przykładowe użycie

### Konwersja do formatu akceptowalnego przez augmentator

Przed augmentacją dane wejściowe muszą być w formacie `text` + `labels`:

```bash
python3 code/dataset/convert_raw_clarin_to_labels.py \
  --input "resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl" \
  --output "resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k_labels.jsonl"
```

### Uruchomienie augmentacji

```bash
genai-data-augmentation \
  --dataset-path="resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k_labels.jsonl" \
  --labels="pozytywny" \
  --output-dir="resources/dataset/twitteremo/augmented" \
  --prompt-file=resources/prompts/augmentation/augmentator.prompt \
  --llm-router-url="http://localhost:8080" \
  --model-name="gpt-oss:120b" \
  --temperature=0.0 \
  --batch-save-size=2 \
  --num-workers=2 \
  --n-sample=350 \
  --n-examples=5 \
  --samples-as-examples=2 \
  --text-column-name="text" \
  --label-column-name="labels"
```

### Kluczowe parametry

| Parametr | Opis | Przykładowa wartość |
|----------|------|---------------------|
| `--dataset-path` | Ścieżka do pliku JSONL (z etykietami) | `..._labels.jsonl` |
| `--labels` | Klasa docelowa do augmentacji | `pozytywny` |
| `--output-dir` | Katalog na wyniki | `resources/dataset/twitteremo/augmented/` |
| `--prompt-file` | Plik promptu augmentatora | `resources/prompts/augmentation/augmentator.prompt` |
| `--llm-router-url` | URL llm-router | `http://localhost:8080` |
| `--model-name` | Nazwa modelu LLM | `gpt-oss:120b` |
| `--n-sample` | Liczba przykładów do augmentacji | `350` |
| `--n-examples` | Liczba wygenerowanych przykładów na jeden input | `5` |
| `--samples-as-examples` | Liczba in-context examples w promptcie | `2` |
| `--temperature` | Temperatura generacji | `0.0` |
| `--text-column-name` | Nazwa kolumny z tekstem | `text` |
| `--label-column-name` | Nazwa kolumny z etykietami | `labels` |
| `--num-workers` | Liczba workerów | `2` |

---

## Wynik augmentacji

Załóżmy, że dla klasy `pozytywny` wybrano 350 przykładów i dla każdego z nich wygenerowano po 5 nowych wersji:

```
Dane wejściowe:
{
  "tekst": "Bardzo się cieszę z tej opinii! Super sprawa!",
  "labels": ["pozytywny"]
}

Wynik augmentacji:
{
  "tekst": "Bardzo się cieszę z tej opinii! Super sprawa!",
  "labels": ["pozytywny"],
  "augmented": [
    "Ta opinia bardzo mnie ucieszyła! Rzeczywiście świetne!",
    "Nie można się nie cieszyć z takiego komentarza! Wow!",
    "Bardzo pozytywnie nastawia ta uwaga! Podoba mi się!",
    "Super sprawa! Ta wiadomość sprawia, że się uśmiecham!",
    "Fajna opinia! Rzetelna i bardzo miła!"
  ]
}
```

---

## Merge z danymi źródłowymi

Augmentowane dane są łączone z oryginalnym datasetem:

```bash
# Merge danych augmentowanych z danymi ręcznymi
bash code/augmentation/04_merge_aug_data_with_manual.sh
```

Efekt: `5000 ręcznych + ~1750 (350×5) augmentowanych = ~6750 przykładów`.

---

## Wizualizacja po merge

```bash
python3 code/dataset/visualize_class_distribution.py \
  --train resources/dataset/twitteremo/merged/...-merged.jsonl \
  --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \
  --output resources/dataset/twitteremo/merged/class_distribution_after_aug.png
```

---

## Optymalizacja wydajności

| Parametr | Wpływ | Rekomendacja |
|----------|-------|--------------|
| `--n-sample` | Liczba przetworzonych przykładów | Zmniejsz do testów (np. `--n-sample=50`) |
| `--n-examples` | Liczba wygenerowanych wariantów na jeden input | `5` to dobry balans |
| `--samples-as-examples` | In-context learning (więcej = lepszy wynik, ale wolniejszy) | `2`–`3` |
| `--num-workers` | Równoległość | Zwiększ na szybkich maszynach |
| `--temperature` | Determinizm | `0.0` dla konsystencji, `0.3`–`0.7` dla różnorodności |

---

Powrót do [agendy](00_agenda.md).
