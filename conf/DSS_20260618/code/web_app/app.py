import torch
import os
import sys
import numpy as np

from pathlib import Path

from sqlalchemy import func
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from flask import Flask, render_template, request, jsonify, current_app

# Resolve paths relative to this file's location
APP_DIR = Path(__file__).resolve().parent  # code/web_app
PROJECT_ROOT = APP_DIR.parent.parent  # conf/DSS_20260618
INSTANCE_DIR = PROJECT_ROOT / "instance"  # instance/
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

# Database path relative to instance/ directory
DB_PATH = INSTANCE_DIR / "data.db"

# Template path relative to this script
TEMPLATE_DIR = APP_DIR / "templates"

from code.web_app.models import db, Example, Annotation

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Cache for loaded models
MODELS = {}
TOKENIZERS = {}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

MODEL_PATHS = {
    "twitter-emo-sample-5k-manual": "/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual",
    "5k-manual+1.7k-augmented": "/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented",
    "5k-m+1.7k-aug+al-live": "/mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k-manual-1_7k-augmented_active_learning",
}


def get_model(model_name):
    path = MODEL_PATHS.get(model_name)
    if not path:
        return None, None

    if model_name not in MODELS:
        try:
            MODELS[model_name] = AutoModelForSequenceClassification.from_pretrained(
                path
            ).to(DEVICE)
            TOKENIZERS[model_name] = AutoTokenizer.from_pretrained(path)
            MODELS[model_name].eval()
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            return None, None

    return MODELS[model_name], TOKENIZERS[model_name]


@app.route("/")
def index():
    return render_template("index.html", models=list(MODEL_PATHS.keys()))


@app.route("/get_example", methods=["GET"])
def get_example():
    model_name = request.args.get("model_name")
    if not model_name:
        return jsonify({"error": "No model selected"}), 400

    # Get random example
    example = Example.query.order_by(func.random()).first()
    if not example:
        return jsonify({"error": "No examples in database"}), 404

    # Automatic annotation with selected model
    model, tokenizer = get_model(model_name)
    model_label = "unknown"
    error_message = None

    if model and tokenizer:
        try:
            inputs = tokenizer(
                example.text, return_tensors="pt", truncation=True, max_length=128
            ).to(DEVICE)
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                prediction = torch.argmax(probs, dim=-1).item()

                # Map prediction to label names (assuming 0: neutralny, 1: negatywny, 2: pozytywny as per trainer)
                mapping = {0: "neutralny", 1: "negatywny", 2: "pozytywny"}
                model_label = mapping.get(prediction, "unknown")
        except Exception as e:
            error_message = f"Błąd podczas inferencji: {e}"
    else:
        error_message = f"Nie można załadować modelu '{model_name}'. Wybierz inny model z listy, aby dokonać oceny."

    return jsonify(
        {
            "id": example.id,
            "text": example.text,
            "model_label": model_label,
            "model_name": model_name,
            "error": error_message,
        }
    )


@app.route("/save_annotation", methods=["POST"])
def save_annotation():
    data = request.json
    example_id = data.get("example_id")
    user_label = data.get("user_label")
    model_label = data.get("model_label")
    model_name = data.get("model_name")

    annotation = Annotation(
        example_id=example_id,
        user_label=user_label,
        model_label=model_label,
        model_name=model_name,
    )
    db.session.add(annotation)
    db.session.commit()

    return jsonify({"status": "success"})


@app.route("/get_stats", methods=["GET"])
def get_stats():
    model_name = request.args.get("model_name")

    # Class distribution from user labels
    dist_query = (
        db.session.query(Annotation.user_label, func.count(Annotation.id))
        .group_by(Annotation.user_label)
        .all()
    )
    distribution = {label: count for label, count in dist_query}

    # Model accuracy and model distribution if model_name is provided
    accuracy = None
    model_distribution = {}
    model_total = 0
    if model_name:
        # Get all annotations for this model
        model_annotations = Annotation.query.filter_by(model_name=model_name).all()
        model_total = len(model_annotations)

        if model_total > 0:
            correct = 0
            for ann in model_annotations:
                # Count distribution
                label = ann.model_label
                model_distribution[label] = model_distribution.get(label, 0) + 1

                # Count correct predictions
                if ann.user_label == ann.model_label:
                    correct += 1

            accuracy = (correct / model_total) * 100

    # Progress stats: annotated vs total
    total_examples = Example.query.count()
    annotated_examples = db.session.query(
        func.count(func.distinct(Annotation.example_id))
    ).scalar()

    return jsonify(
        {
            "distribution": distribution,
            "accuracy": accuracy,
            "model_distribution": model_distribution,
            "model_total": model_total,
            "total_examples": total_examples,
            "annotated_examples": annotated_examples,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
