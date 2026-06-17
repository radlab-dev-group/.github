# DSS 2026 — Augmentacja danych uczących dla modeli klasyfikacyjnych z wykorzystaniem lokalnych LLMów

---

- Link do strony: [klik](https://dss2026.radlab.dev/)
- Link do agendy/opisu procesu: [klik](presentation/md/00_agenda.md)

---

Projekt przygotowany w ramach Tutorials DSS 2026, dotyczący augmentacji zbioru treningowego.
W przykładach wykorzystan został `clarin-pl/twitteremo`, który augmentowany był za pomocą lokalnych LLMów (GPT-oss
120B). Dane ręcznie przygotowane (CLARIN-PL), wzbogacone o dane augmentowane wykorzystane zostały do trenowania
klasyfikatora polaryzacji emocjonalnej (polaryzacja: pozytywny / negatywny / neutralny) w wariantach:

1. Próbka danych uczących z ręcznymi anotacjami (problem rozpoznawania klasy `pozytywny`);
2. Próbka danych uczących wzbogacona o dane augmentowane dla klasy `pozytywny`;
3. Anotacja LIVE - poprawa danych augmentowanych;

## Zakres

- **Augmentacja danych**: Wygenerowanie dodatkowych przykładów treningowych dla klasyfikacji polaryzacji emocjonalnej z
  wykorzystaniem `genai-classifier` i LLM `gpt-oss:120b`.
- **Fine-tuning modelu**: Trenowanie klasyfikatora polaryzacji tekstu na zmieszanej bazie (oryginał 5k + augmentacja ~
  1.7k) z modelem bazowym `allegro/herbert-base-cased`.
- **Web App**: Interfejs wizualnej oceny predykcji modelu z możliwością ręcznej anotacji.

## Pipeline zbioru danych

```
0. Przygotowanie datasetu bazowego (00_prepare_base_dataset.sh)
   Pobranie i próbkowanie datasetu TwitterEmo (HF)
   → 5k train + 500 valid samples (JSONL)

1. Trenowanie modelu bazowego na danych manualnych (01_train_base_manual.sh)
   Herbert Base, 5 epok, LR=3e-6
   → Model wariant 1 (tylko dane ręczne)

2. Przygotowanie danych augmentowanych (02_prepare_augmented_data.sh)
   Labelowanie LLM, selekcja klasy, generowanie nowych przykładów
   → ~1.7k dodatkowych przykładów dla klasy `pozytywny`

3. Merge datasetów (03_merge_augmented_data_with_manual.sh)
   Połączenie 5k manualnych + ~1.7k augmentowanych
   → Mieszany zbiór treningowy

4. Trenowanie modelu na danych mieszanych (04_train_base_manual_with_aug_1_7k.sh)
   Herbert Base, 5 epok, LR=3e-6
   → Model wariant 2 (dane ręczne + augmentacja)

5. Import danych do web app (05_import_data_to_web.sh)
   Import augmentowanych przykładów do bazy SQLite do wizualnej oceny

6. Uruchomienie web app (06_run_web_app.sh)
   → Wizualna ocena + ręczna anotacja; dane z bazy zalewane do datasetu

7. Zrzut z web app i finetuning (07_web_app_dump_data_and_run_training.sh)
   Zrzut decyzji użytkowników z bazy Flask, merge z danymi augmentowanymi, ponowny trening
   → Model wariant 3 (z aktywnym uczeniem / HIL)
```

## Struktura i zawartość repozytorium

| Directory                                | Description                                                      |
|------------------------------------------|------------------------------------------------------------------|
| [code](code/)                            | Zobacz `code/README.md` po szczegółowy opis narzędzi             |
| [code/dataset](code/dataset/)            | Pobieranie, konwersja, wizualizacja rozkładu klas                |
| [code/training](code/training/)          | Fine-tuning classifier polaryzacji (HF Trainer API + W&B)        |
| [code/augmentation/](code/augmentation/) | Skrypty augmentacji: labelowanie LLM, selekcja klas, generowanie |
| [code/web_app/](code/web_app/)           | Flask app: wizualna ocena + anotacja modelu                      |
| [instance/](instance/)                   | Baza SQLite (Flask web app)                                      |
| [presentation/md/](presentation/md/)     | Slajdy prezentacji (markdown)                                    |
| [presentation/pptx/](presentation/pptx/) | Szablon PowerPoint prezentacji                                   |
| [presentation/imgs/](presentation/imgs/) | Obrazki do prezentacji                                           |
| [resources/dataset/](resources/dataset/) | Dataset samples (JSONL), augmented data, wizualizacje            |
| [resources/prompts/](resources/prompts/) | Prompty dla LLM (klasyfikator + augmentator)                     |

## Wymagania

```bash
pip install -r requirements.txt
```

Główne zależności: `torch`, `transformers`, `datasets`, `scikit-learn`, `matplotlib`, `wandb`, `flask`,
`flask_sqlalchemy`

## Pełne odtworzenie prezentowanego środowiska

### 0. Przygotowanie datasetu bazowego

```bash
bash 00_prepare_base_dataset.sh
```

Pobiera dataset `clarin-pl/twitteremo` z HuggingFace i tworzy próbkę:

- **5000** przykładów treningowych → `resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl`
- **500** przykładów walidacyjnych → `resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl`

### 1. Trenowanie modelu bazowego (dane manualne)

```bash
bash 01_train_base_manual.sh
```

Trenuje `allegro/herbert-base-cased` na ręcznych anotacjach (5k train + 500 valid).

### 2. Przygotowanie danych augmentowanych

```bash
bash 02_prepare_augmented_data.sh
```

Generuje ~1.7k dodatkowych przykładów dla klasy `pozytywny` przy użyciu `genai-data-augmentation` i LLM `gpt-oss:120b`.

### 3. Merge danych augmentowanych

```bash
bash 03_merge_augmented_data_with_manual.sh
```

Łączy 5k danych ręcznych z ~1.7k augmentowanymi w jeden zbiór treningowy.

### 4. Trenowanie modelu na danych mieszanych

```bash
bash 04_train_base_manual_with_aug_1_7k.sh
```

Trenuje model na zmieszanej bazie (5k manual + ~1.7k augmentowanych).

### 5. Import danych do web app

```bash
bash 05_import_data_to_web.sh
```

Importuje dane augmentowane do bazy SQLite w web app — gotowe do wizualnej oceny.

### 6. Uruchomienie web app

```bash
bash 06_run_web_app.sh
```

Otwiera interfejs wizualnej oceny predykcji z możliwością ręcznej anotacji.

### 7. Zrzut z web app i finetuning (wariant z aktywnym uczeniem)

```bash
bash 07_web_app_dump_data_and_run_training.sh
```

Kroki wewnątrz skryptu:

1. **Zrzut danych** — eksport decyzji użytkowników z bazy SQLite Flask (`active_learning` JSONL)
2. **Merge** — połączenie zrzutu z oryginalnym datasetem (5k)
3. **Wizualizacja rozkładu klas** — dla zrzutu i merged datasetu (obrazy PNG)
4. **Finetuning** — trening na danych ręcznych + augmentowanych + aktywnie wzbogaconych (HIL)
    - Model bazowy: `allegro/herbert-base-cased`
    - 5 epok, LR=3e-6, batch=32, cosine scheduler
    - Output: checkpoint z aktywnym uczeniem (wariant 3)

## Wyniki

- Fine-tunowany model `allegro/herbert-base-cased` (3 klasy: neutralny / negatywny / pozytywny)
- Trening: 5 epok, LR=3e-6, batch=32, gradient_accumulation=2, cosine scheduler
- Ocena: accuracy + macro F1 + confusion matrix (+logowane do W&B)

## Links

- [Agenda](presentation/md/00_agenda.md) — overview prezentacji
- [code/README.md](code/README.md) — szczegółowa dokumentacja narzędzi dataset / training / web app
