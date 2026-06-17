# Uczenie — pełny opis treningu

Powrót do [agendy](00_agenda.md).

---

## Zbiór danych

W ramach tutorialu wykorzystano dataset **clarin-pl/twitteremo** z HuggingFace:

- `clarinpl-twitteremo-train-sample-5k.jsonl` — zbiór treningowy (5000 próbek)
- `clarinpl-twitteremo-valid-sample-500.jsonl` — zbiór walidacyjny (500 próbek)

Oba zbiory to losowe próbki z [`clarin-pl/twitteremo`](https://huggingface.co/datasets/clarin-pl/twitteremo),
zawierające teksty z Twittera z anotacjami polaryzacji emocjonalnej.

Klasy:

| Klasa           | Opis                                  |
|-----------------|---------------------------------------|
| `neutralny` (0) | Tekst bez wyraźnej emocji, obiektywny |
| `negatywny` (1) | Tekst z emocjami negatywnymi          |
| `pozytywny` (2) | Tekst z emocjami pozytywnymi          |

---

## Model bazowy

**`allegro/herbert-base-cased`** — polski model bazowy z HuggingFace:

- Architektura: BERT (Transformer encoder)
- Waga: ~135M parametrów
- Fine-tuning do klasyfikacji 3-klasowej (polaryzacja emocjonalna)

---

## Parametry treningu (wszystkie warianty)

| Parametr                  | Wartość                      | Opis                                 |
|---------------------------|------------------------------|--------------------------------------|
| **Model bazowy**          | `allegro/herbert-base-cased` | BERT dla polskiego                   |
| **Eoki**                  | 5                            | Liczba pełnych przejść przez dataset |
| **Batch size**            | 32                           | Liczba przykładów na iterację        |
| **Learning rate**         | 3e-6                         | Małe LR dla stabilnego fine-tuningu  |
| **Max length**            | 128                          | Maksymalna długość sekwencji tokenów |
| **Gradient accumulation** | 2                            | Efektywny batch = 64                 |
| **Scheduler**             | Cosine                       | Cosine annealing LR                  |
| **Seed**                  | 42                           | Reprodukowalność                     |
| **Logowanie**             | W&B (Weights & Biases)       | accuracy, loss, F1, confusion matrix |

---

## Warianty modeli

W ramach tutorialu wytrenowano **3 modele** warianty, pokazujące postęp po każdej iteracji pipeline'u.

### Wariant 1: Tylko dane manualne (5k)

```bash
bash 01_train_base_manual.sh
```

- **Dane treningowe:** `clarinpl-twitteremo-train-sample-5k.jsonl` (5000 ręcznych)
- **Dane walidacyjne:** `clarinpl-twitteremo-valid-sample-500.jsonl` (500)
- **Model output:** `twitter-emo-sample-5k-manual`

> Baseline — model uczony tylko na ręcznych anotacjach.

### Wariant 2: Dane manualne + augmentacja (~1.7k)

```bash
bash 04_train_base_manual_with_aug_1_7k.sh
```

- **Dane treningowe:** `merged/clarinpl-twitteremo-train-sample-5k-and-augmented-pos-1_7k.jsonl`
  (5000 ręcznych + ~1750 augmentowanych)
- **Dane walidacyjne:** `clarinpl-twitteremo-valid-sample-500.jsonl` (500)
- **Model output:** `twitter-emo-sample-5k-manual-1_7k-augmented`

> Dane augmentowane dla klasy `pozytywny` (`genai-data-augmentation` → 350 samples × 5 wariantów).

### Wariant 3: Dane manualne + augmentacja + HIL/AL

```bash
bash 07_web_app_dump_data_and_run_training.sh
```

- **Dane treningowe:** `active_learning/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning.jsonl`
  (5000 ręcznych + ~1750 augmentowanych + dane z Web App)
- **Dane walidacyjne:** `clarinpl-twitteremo-valid-sample-500.jsonl` (500)
- **Model output:** `twitter-emo-sample-5k-manual-1_7k-augmented_active_learning`

> Dane z Web App — użytkownicy poprawiali etykiety augmentowanych przykładów (HIL/AL).

---

## Pipeline treningu (skrypt `train_polarity_model.py`)

Skrypt znajduje się w `code/training/train_polarity_model.py`.

### Etapy:

1. **Ładowanie danych** — JSONL z polami `tekst` i `labels` (JSON array).
2. **Tokenizacja** — HERBERT tokenizer z paddingiem dynamicznym.
3. **Inicjalizacja modelu** — `AutoModelForSequenceClassification.from_pretrained()` z 3 klasami.
4. **TrainingArguments** — HuggingFace Trainer z cosine scheduler, W&B logging.
5. **Trening** — `Trainer.train()` na 5 epok.
6. **Ewaluacja** — accuracy + macro F1 + confusion matrix.
7. **Zapis modelu** — `model.save_pretrained()` + `tokenizer.save_pretrained()`.

### Metryki:

| Metryka               | Opis                                      |
|-----------------------|-------------------------------------------|
| **Accuracy**          | Ogólna poprawność (wszystkie klasy razem) |
| **Precision (macro)** | Średnia precyzja po klasach               |
| **Recall (macro)**    | Średnia czułość po klasach                |
| **F1-score (macro)**  | Średnia ważona F1 po klasach              |
| **Confusion matrix**  | Macierz pomyłek — które klasy są mylone   |

Wszystkie metryki logowane do **Weights & Biases** w czasie rzeczywistym.

---

## Dane po HIL/AL — wybór etykiety (dump_dataset_from_web_app.py)

Po anotacji w Web App, skrypt `code/dataset/dump_dataset_from_web_app.py` tworzy ostateczny dataset treningowy:

1. **Pobiera wszystkie przykłady** z bazy SQLite (tabela `Example`).
2. **Dla każdego tekstu** sprawdza powiązane anotacje (tabela `Annotation`):

| Scenariusz                       | Działanie                                              |
|----------------------------------|--------------------------------------------------------|
| Brak ręcznych anotacji           | Predykcja modelu (wariant 2) → etykieta automatyczna   |
| Dokładnie jedna ręczna anotacja  | Użyta bezpośrednio                                     |
| Więcej niż jedna ręczna anotacja | Majority voting (głosowanie większościowe)             |
| Remis w głosowaniu               | Tie-breaker: predykcja modelu jako głos rozstrzygający |

3. **Formatowanie** — dla każdej klasy (`pozytywny`, `negatywny`, `neutralny`) tworzy kolumnę binarną (1 = tak, 0 =
   nie).

---

## Struktura plików treningowych

```
resources/dataset/twitteremo/
├── clarinpl-twitteremo-train-sample-5k.jsonl              # Bazowy zbiór (5k)
├── clarinpl-twitteremo-train-sample-5k_labels.jsonl       # Po labelowaniu genai-classifier
├── clarinpl-twitteremo-valid-sample-500.jsonl             # Zbiór walidacyjny (500)
├── genailabelled/
│   ├── ..._clean_labels.jsonl                             # Wynik genai-classifier
│   └── ..._training.jsonl                                 # Po konwersji do formatu treningowego
├── augmented/
│   ├── ..._augmented.jsonl                                # Wynik genai-data-augmentation
│   └── ..._training.jsonl                                 # Po konwersji do formatu treningowego
├── merged/
│   ├── ...-and-augmented-pos-1_7k.jsonl                   # Merge: 5k + ~1.7k
│   └── ...-and-augmented-pos-1_7k.png                     # Wizualizacja rozkładu klas
└── active_learning/
    ├── ..._active_learning.jsonl                          # Dump z Web App + merge
    ├── ..._active_learning-training.jsonl                 # Ostateczny zbiór treningowy
    └── ..._training.png                                   # Wizualizacja rozkładu klas
```

---

## Wyniki — porównanie wariantów

| Wariant | Dane treningowe    | Accuracy        | Macro F1        |
|---------|--------------------|-----------------|-----------------|
| **1**   | 5k manual          | → podgląd w W&B | → podgląd w W&B |
| **2**   | 5k + ~1.7k augment | → podgląd w W&B | → podgląd w W&B |
| **3**   | 5k + ~1.7k + HIL   | → podgląd w W&B | → podgląd w W&B |

Pełne wyniki dostępne na żywo: **[dss2026.radlab.dev](https://dss2026.radlab.dev/)
** + [Weights & Biases](https://wandb.ai/).

---

Powrót do [agendy](00_agenda.md).
