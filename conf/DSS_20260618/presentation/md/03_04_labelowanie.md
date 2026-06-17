# Automatyczne labelowanie za pomocą utilsów

Powrót do [agendy](00_agenda.md).

---

## Czym jest `genai-classifier`?

`genai-classifier` to CLI z pakietu **[llm-router-utils](https://github.com/radlab-dev-group/llm-router-utils)**,
służący do automatycznego oznaczania danych tekstowych dowolnymi klasami z wykorzystaniem LLM (modeli generatywnych).
Zasada działania jest następująca:

1. Pobiera zbiór danych wejściowych (JSONL / XLSX / HF datasets).
2. Dla każdego przykładu wysyła prompt do LLM (przez llm-router).
3. LLM zwraca klasę/przypisaną etykietę.
4. Wyniki są zapisywane do pliku JSONL z dodatkowym polem `labels`.

```
┌──────────────────────┐
│   dane wejściowe     │
│   (JSONL, bez label) │
└──────────┬───────────┘
           │
           ▼
┌────────────────────────┐
│   genai-classifier     │
│                        │
│  dla każdego przykładu:│
│  1. buduje prompt      │
│  2. wysyła do LLM      │
│  3. parsuje wynik      │
│                        │
│  • batch processing    │
│  • wielowątkowość      │
│  • retry on error      │
└──────────┬─────────────┘
           │
           ▼
┌──────────────────────┐
│   dane wyjściowe     │
│   (JSONL, z labels)  │
└──────────────────────┘
```

---

## Instalacja (z pakietu llm-router-utils)

```bash
git clone https://github.com/radlab-dev-group/llm-router-utils.git
cd llm-router-utils
pip install -e .
pip install ".[llm-router]"   # llm-router + llm-router-services z git
```

Po instalacji `genai-classifier` jest dostępny jako komenda CLI w systemie.

---

## Przykładowe użycie

### Uruchomienie labelowania

```bash
genai-classifier \
  --dataset-dir="resources/dataset/twitteremo/" \
  --prompts-dir=resources/prompts/classifier \
  --output-dir=resources/dataset/twitteremo/genailabelled \
  --llm-router-url="http://localhost:8080" \
  --model-name="gpt-oss:120b" \
  --temperature=0.0 \
  --batch-save-size=2 \
  --num-workers=2 \
  --n-sample=0 \
  --text-column-name="tekst"
```

### Kluczowe parametry

| Parametr             | Opis                                           | Przykładowa wartość                           |
|----------------------|------------------------------------------------|-----------------------------------------------|
| `--dataset-dir`      | Katalog z danymi wejściowymi (JSONL)           | `resources/dataset/twitteremo/`               |
| `--prompts-dir`      | Katalog z promptami                            | `resources/prompts/classifier/`               |
| `--output-dir`       | Katalog na wyniki                              | `resources/dataset/twitteremo/genailabelled/` |
| `--llm-router-url`   | URL llm-router                                 | `http://localhost:8080`                       |
| `--model-name`       | Nazwa modelu LLM                               | `gpt-oss:120b`                                |
| `--temperature`      | Temperatura (0 = deterministyczne)             | `0.0`                                         |
| `--num-workers`      | Liczba workerów (wielowątkowość)               | `2`                                           |
| `--n-sample`         | Liczba próbkowanych przykładów (0 = wszystkie) | `0`                                           |
| `--text-column-name` | Nazwa kolumny z tekstem                        | `tekst`                                       |
| `--batch-save-size`  | Rozmiar batcha do zapisu                       | `2`                                           |

Wykaz wszystkich parametrów wraz z opisem dostępny jest jako:

```shell
genai-classifier --help

usage: genai-classifier [-h] --dataset-dir DATASET_DIR --prompts-dir PROMPTS_DIR [--llm-router-url LLM_ROUTER_URL] [--model-name MODEL_NAME] [--temperature TEMPERATURE] [--batch-save-size BATCH_SAVE_SIZE] [--dry-run] [--output-dir OUTPUT_DIR] [--verbose] [--num-workers NUM_WORKERS] [--n-sample N_SAMPLE]
                        [--text-column-name TEXT_COLUMN_NAME] [--export-xlsx] [--no-export-xlsx]

Classify translated datasets using LLMRouter.

options:
  -h, --help            show this help message and exit
  --dataset-dir DATASET_DIR
                        Directory containing downloaded HF datasets.
  --prompts-dir PROMPTS_DIR
                        Directory with prompt files.
  --llm-router-url LLM_ROUTER_URL
                        Base URL of the LLMRouter service.
  --model-name MODEL_NAME
                        Model identifier passed to the router.
  --temperature TEMPERATURE
                        Sampling temperature for the model.
  --batch-save-size BATCH_SAVE_SIZE
                        How many aggregated records are written to disk at once.
  --dry-run             Process data but do not write output files.
  --output-dir OUTPUT_DIR
                        Override directory where result .jsonl files are stored.
  --verbose             Enable DEBUG level logging.
  --num-workers NUM_WORKERS
                        Number of parallel worker threads (and LLM clients).
  --n-sample N_SAMPLE   Number of random samples per field (default: all). If omitted, zero or negative, all examples are processed.
  --text-column-name TEXT_COLUMN_NAME
                        Name of the column containing the text to classify (default: 'Tekst').
  --export-xlsx         Convert output JSONL files to XLSX format (default: True).
  --no-export-xlsx      Disable XLSX export (only save JSONL files).
```

---

## Konwersja wyniku do formatu treningowego

Dane wyjściowe z `genai-classifier` wymagają konwersji do formatu akceptowalnego przez skrypt treningowy:

```bash
python3 code/dataset/convert_genai_to_training.py \
  --input resources/dataset/twitteremo/genailabelled/clarinpl-twitteremo-train-sample-5k_clean_labels.jsonl \
  --output resources/dataset/twitteremo/genailabelled/clarinpl-twitteremo-train-sample-5k_training.jsonl
```

Ten skrypt mapuje:

| Klucz w JSONL | Opis                                          |
|---------------|-----------------------------------------------|
| `tekst`       | Tekst przykładu                               |
| `labels`      | Lista etykiet (np. `["pozytywny"]`)           |
| `prediction`  | Predykcja LLM (Pozytywna/Negatywna/Neutralna) |

Konwersja mapuje tekstowe etykiety na format binarny (pozytywny / negatywny / neutralny) wymagany przez
`train_polarity_model.py`.

---

## Przykład promptu klasyfikatora

Prompty dla klasyfikatora znajdują się w katalogu `resources/prompts/classifier/`. Przykładowy prompt:

```text
Jesteś precyzyjnym anotatorem analizującym tekst pod kątem **polaryzacji emocjonalnej**.
Twoim jedynym zadaniem jest określić, do której z trzech klas należy podany tekst: **Pozytywna**, **Negatywna** lub **Neutralna**.
Wynik musisz zwrócić w ściśle określonym formacie JSON.

**Klasy (definicje)**
- **Pozytywna** – Tekst wyraża przyjazne, optymistyczne lub pochwalne emocje. Zawiera pochwały, radość, entuzjazm, satysfakcję, podziękowania itp.
- **Negatywna** – Tekst wyraża nieprzyjemne, krytyczne lub złościwe emocje. Zawiera skargi, ironię, gniew, smutek, rozczarowanie, oburzenie itp.
- **Neutralna** – Tekst nie niesie wyraźnego ładunku emocjonalnego albo jest czysto informacyjny, opisowy, faktograficzny. Nie można go jednoznacznie zakwalifikować do klasy pozytywnej ani negatywnej.

**Zasady działania**
1. Przejrzyj cały otrzymany tekst.
2. Jeśli znajdziesz przynajmniej jeden wyraźny sygnał emocjonalny zgodny z definicją klasy **Pozytywna** lub **Negatywna**, przypisz tę klasę.
3. W przypadku konfliktu (tekst zawiera zarówno pozytywne, jak i negatywne elementy) – wybierz klasę, której sygnałów jest więcej.
4. Jeśli żaden wyraźny sygnał nie występuje, przypisz klasę **Neutralna**.
5. Podaj krótkie uzasadnienie (maksymalnie 30 słów) odwołujące się bezpośrednio do najważniejszych elementów tekstu.
6. Oszacuj pewność decyzji w skali 0.0‑1.0 (im wyraźniejsze wskazówki, tym bliżej 1.0).

**Specjalny przypadek – pusty lub nieczytelny tekst**

{
  "exists": false,
  "class": "Neutralna",
  "confidence": 1.0,
  "reason": "Tekst pusty lub nie zawiera treści do oceny"
}

**Format wyjścia (JSON) – jedno poprawne JSON‑owe wyjście na każde zapytanie**
{
  "exists": true, // true, gdy tekst istnieje; false w sytuacji pustego/nieczytelnego tekstu
  "class": "Pozytywna" | "Negatywna" | "Neutralna",
  "confidence": 0.0-1.0, // szacowana pewność decyzji
  "reason": "Krótka przyczyna decyzji" // maksymalnie 30 słów
}

Zwróć wynik w dokładnie określonym formacie JSON – **bez żadnego dodatkowego tekstu przed lub po**.
```

---

## Oszczędzanie kosztów / czasu

- `--n-sample=0` — przetwarza **wszystkie** przykłady (przy 5k przykładów = 5k wywołań LLM).
- `--n-sample=N` — przetwarza **tylko N** przykładów (do testów/próbek).
- `--num-workers=2` — zwiększa przepustowość przetwarzania (więcej workerów = szybciej, ale więcej obciążenia na LLM i
  większe zasoby są potrzebne).
- `--temperature=0.0` — deterministyczne wyniki, co jest ważne dla spójności generowanych labelek.

---

Powrót do [agendy](00_agenda.md).
