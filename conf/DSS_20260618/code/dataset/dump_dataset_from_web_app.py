import torch
import json
import os
import sys
from pathlib import Path
from sqlalchemy import func
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from collections import Counter
from tqdm import tqdm

# Dodanie katalogu głównego projektu do ścieżki, aby móc importować modele bazy danych
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from code.web_app.models import db, Example, Annotation, create_app

"""
ALGORITHM OPIS WYBORU PRZYKŁADU DO DUMPA:
1. Skrypt pobiera wszystkie rekordy z tabeli 'Example' w bazie danych.
2. Dla każdego tekstu sprawdzane są powiązane z nim anotacje w tabeli 'Annotation'.
3. Scenariusze wyboru klasy:
    a) Brak ręcznych anotacji:
       Tekst jest przepuszczany przez model "--model=5k-manual+1.7k-augmented". 
       Zwrócona etykieta modelu staje się klasą docelową.
    b) Dokładnie jedna ręczna anotacja:
       Używana jest etykieta podana przez człowieka.
    c) Więcej niż jedna ręczna anotacja:
       Stosowane jest głosowanie większościowe (majority voting).
       Wybierana jest klasa, która pojawia się najczęściej wśród ludzkich ocen.
    d) Remis w głosowaniu ręcznym (np. 50-50):
       Jako głos rozstrzygający (tie-breaker) używana jest decyzja modelu "--model=5k-manual+1.7k-augmented".
       Wygrywa klasa wskazana przez model, o ile była ona jedną z remisujących klas w głosowaniu ludzkim, 
       w przeciwnym razie brana jest po prostu pod uwagę jako dodatkowy głos w ogólnej puli.
4. Formatowanie:
   Wybrana klasa otrzymuje wartość 1, pozostałe klasy podstawowe (pozytywny, negatywny, neutralny) otrzymują 0.
   Wszystkie dodatkowe klasy emocji (radość, smutek, itp.) są ustawiane na 0 zgodnie z wymaganiami.
"""

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented"
DEFAULT_OUTPUT_FILE = (
    PROJECT_ROOT
    / "resources"
    / "dataset"
    / "twitteremo"
    / "active_learning"
    / "active_learning_dump.jsonl"
)


def load_model(model_name):
    if model_name and Path(model_name).exists():
        try:
            print(f"Loading model from {model_name} on {DEVICE}...")
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name
            ).to(DEVICE)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model.eval()
            return model, tokenizer
        except Exception as e:
            print(f"Warning: Could not load model from {model_name}: {e}")
    print("Cannot found model")


def predict(text, model, tokenizer):
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=128
    ).to(DEVICE)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        prediction = torch.argmax(probs, dim=-1).item()
        # Mapping: 0: neutralny, 1: negatywny, 2: pozytywny (zgodnie z app.py)
        mapping = {0: "neutralny", 1: "negatywny", 2: "pozytywny"}
        return mapping.get(prediction, "unknown")


def dump_dataset(model_path=None, output_path=None):
    app = create_app()
    model, tokenizer = load_model(model_path)

    if output_path is None:
        output_path = DEFAULT_OUTPUT_FILE

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    classes = ["pozytywny", "negatywny", "neutralny"]
    emotions = [
        "radość",
        "smutek",
        "zaufanie",
        "wstręt",
        "strach",
        "gniew",
        "przeczuwanie",
        "zdziwienie",
        "ambiwalentny",
        "sarkazm",
    ]

    with app.app_context():
        examples = Example.query.all()
        print(f"Found {len(examples)} examples to process.")

        manual_count = 0
        model_count = 0

        with open(output_path, "w", encoding="utf-8") as f:
            for ex in tqdm(examples, desc="Dumping dataset"):
                annotations = Annotation.query.filter_by(example_id=ex.id).all()
                user_labels = [a.user_label for a in annotations if a.user_label]

                final_label = None

                if not user_labels:
                    # Case 1: No manual annotation
                    final_label = predict(ex.text, model, tokenizer)
                    model_count += 1
                elif len(user_labels) == 1:
                    # Case 2.1: One manual annotation
                    final_label = user_labels[0]
                    manual_count += 1
                else:
                    # Case 2.2: Multiple annotations
                    manual_count += 1
                    counts = Counter(user_labels)
                    most_common = counts.most_common()

                    if (
                        len(most_common) > 1
                        and most_common[0][1] == most_common[1][1]
                    ):
                        # Case 2.2.a: Tie (50-50 or similar)
                        model_label = predict(ex.text, model, tokenizer)
                        # Add model's vote to the pool and re-evaluate
                        user_labels.append(model_label)
                        final_label = Counter(user_labels).most_common(1)[0][0]
                    else:
                        final_label = most_common[0][0]

                # Build result object
                result = {"text": ex.text}
                for cls in classes:
                    result[cls] = 1 if cls == final_label else 0
                for emo in emotions:
                    result[emo] = 0

                f.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"\nExport finished. Saved to {output_path}")
    print(f"Summary statistics:")
    print(f"  - Total examples: {len(examples)}")
    print(f"  - Manual annotations used: {manual_count}")
    print(f"  - Model predictions used: {model_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path", default=MODEL_PATH, help="Path to the model for predictions"
    )
    parser.add_argument(
        "--output-path",
        default=str(DEFAULT_OUTPUT_FILE),
        help="Path to the output JSONL file",
    )
    args = parser.parse_args()

    dump_dataset(args.model_path, args.output_path)
