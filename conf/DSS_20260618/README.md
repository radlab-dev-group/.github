# DSS 2026 — Augmentacja danych uczących dla modeli klasyfikacyjnych z wykorzystaniem lokalnych LLMów

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
1. Pobranie datasetu (clarin-pl/twitteremo, HF)
   → 5k train + 500 valid samples (JSONL)

 1.1. Labelowanie przez LLM (genai-classifier + gpt-oss:120b)
      (dlaczego trzeba kontrolować dane po augmentacji?)
      → Anotacja tekstu w klasy: Pozytywna / Negatywna / Neutralna

2. Augmentacja danych (genai-data-augmentation + gpt-oss:120b)
   → Generowanie nowych przykładów dla klasy `pozytywne`

3. Merge datasetów (5k + ~1.7k augmented)
   → Mieszany zbiór treningowy

4. Fine-tuning modelu (Herbert Base, 5 epok)
   → Model checkpoint (best model at end, eval_f1_macro)

5. Web App — ocena predykcji
```

## Struktura i zawartość repozytorium

| Directory                                        | Description                                                      |
|--------------------------------------------------|------------------------------------------------------------------|
| [code](code/)                                    | Zobacz `code/README.md` po szczegółowy opis narzędzi             |
| [code/dataset](code/dataset/)                    | Pobieranie, konwersja, wizualizacja rozkładu klas                |
| [code/training](code/training/)                  | Fine-tuning classifier polaryzacji (HF Trainer API + W&B)        |
| [code/augmentation/](code/augmentation/)         | Skrypty augmentacji: labelowanie LLM, selekcja klas, generowanie |
| [code/web_app/](code/web_app/)                   | Flask app: wizualna ocena + anotacja modelu                      |
| [instance/](instance/)                           | Baza SQLite (Flask web app)                                      |
| [output/polarity-model/](output/polarity-model/) | Zapisane checkpointy i model fine-tunowany                       |
| [presentation/md/](presentation/md/)             | Slajdy prezentacji (markdown)                                    |
| [presentation/pptx/](presentation/pptx/)         | Szablon PowerPoint prezentacji                                   |
| [presentation/imgs/](presentation/imgs/)         | Obrazki do prezentacji                                           |
| [resources/dataset/](resources/dataset/)         | Dataset samples (JSONL), augmented data, wizualizacje            |
| [resources/prompts/](resources/prompts/)         | Prompty dla LLM (klasyfikator + augmentator)                     |

## Wymagania

```bash
pip install -r requirements.txt
```

Główne zależności: `torch`, `transformers`, `datasets`, `scikit-learn`, `matplotlib`, `wandb`, `flask`,
`flask_sqlalchemy`

## Uruchomienie

### 1. Trenowanie modelu bazowego

```bash
bash 01_train_base_manual.sh
# lub z augmentacją (~1.7k dodatkowych przykładów):
bash 04_train_base_manual_with_aug_1_7k.sh
```

### 2. Augmentacja danych

```bash
bash code/augmentation/01_label_with_genai.sh   # Anotacja LLM
bash code/augmentation/02_select_class_to_augmentation.sh   # Selekcja klas
bash code/augmentation/03_examples_augemntation.sh  # Generowanie przykładów
```

### 3. Web App - HITL/AL

```bash
# Uruchomienie aplikacji Flask
bash code/web_app/run_app.sh

# Import danych do bazy
bash code/web_app/import_to_db.sh path/to/data.jsonl
```

## Wyniki

- Fine-tunowany model `allegro/herbert-base-cased` (3 klasy: neutralny / negatywny / pozytywny)
- Trening: 5 epok, LR=3e-6, batch=32, gradient_accumulation=2, cosine scheduler
- Ocena: accuracy + macro F1 + confusion matrix (+logowane do W&B)

## Links

- [Agenda](presentation/md/00_agenda.md) — overview prezentacji
- [code/README.md](code/README.md) — szczegółowa dokumentacja narzędzi dataset / training / web app
