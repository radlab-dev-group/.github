"""
Train a polarity classification model (positive / negative / neutral)
on the twitteremo dataset samples using the HuggingFace Trainer API.

Usage:

    python3 code/training/train_polarity_model.py \\
        --train resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \\
        --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \\
        --base-model-path radlab/polish-cross-encoder \\
        --wandb-project polar-twitteremo

"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import numpy as np
import torch
import wandb
from datasets import Dataset as HFDataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EvalPrediction,
    TrainingArguments,
    Trainer,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LABEL_MAP = {0: "neutralny", 1: "negatywny", 2: "pozytywny"}
LABEL_NAMES = list(LABEL_MAP.values())
NUM_LABELS = len(LABEL_NAMES)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_samples(path: Path) -> HFDataset:
    """Load samples from a JSONL file into a HuggingFace Dataset.

    Parameters
    ----------
    path : Path
        Path to the JSONL file.

    Returns
    -------
    HFDataset
        Dataset with ``text`` (str) and ``label`` (int) columns.
    """
    samples: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            label = _to_label(obj)
            if label is not None:
                samples.append({"text": obj["tekst"], "label": label})
    return HFDataset.from_list(samples)


def _to_label(obj: dict) -> int | None:
    """Convert multi-label columns to a single class index.

    Returns
    -------
    int | None
        Class index (0=neutralny, 1=negatywny, 2=pozytywny) or
        ``None`` when all labels are zero.
    """
    p, n, ne = obj.get("pozytywny", 0), obj.get("negatywny", 0), obj.get("neutralny", 0)
    if n == 1:
        return 1
    if p == 1:
        return 2
    if ne == 1:
        return 0
    return None


def _load_and_tokenize(
    path: Path,
    tokenizer: AutoTokenizer,
    max_length: int,
) -> HFDataset:
    """Load a JSONL file and tokenize it.

    Returns raw dicts (no set_format) to avoid numpy 2.x / datasets
    incompatibility; conversion to tensors is handled by the DataCollator.

    Parameters
    ----------
    path : Path
        Path to the JSONL file.
    tokenizer : AutoTokenizer
        Tokenizer for the base model.
    max_length : int
        Maximum sequence length for padding / truncation.

    Returns
    -------
    HFDataset
        Tokenized dataset with ``input_ids`` and ``attention_mask``.
    """
    hf_ds = _load_samples(path)
    hf_ds = hf_ds.map(
        lambda example: tokenizer(
            example["text"],
            max_length=max_length,
            truncation=True,
        ),
        batched=True,
        remove_columns=["text"],
    )
    return hf_ds


def _token_collate(
    features: list[dict],
) -> Dict[str, torch.Tensor]:
    """Convert feature dicts to batched torch tensors.

    Parameters
    ----------
    features : list[dict]
        List of feature dicts from the dataset.

    Returns
    -------
    dict[str, torch.Tensor]
        Batched tensors with ``input_ids``, ``attention_mask``, ``labels``.
    """
    input_ids = torch.stack([torch.tensor(f["input_ids"]) for f in features])
    attention_mask = torch.stack([torch.tensor(f["attention_mask"]) for f in features])
    labels = torch.tensor([f["label"] for f in features])
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def _compute_metrics(p: EvalPrediction) -> Dict[str, float]:
    """Compute accuracy and macro F1 from evaluation predictions.

    Parameters
    ----------
    p : EvalPrediction
        Prediction and label arrays from the Trainer.

    Returns
    -------
    dict[str, float]
        Computed metrics.
    """
    preds = np.argmax(p.predictions, axis=1)
    acc = accuracy_score(p.label_ids, preds)
    f1 = f1_score(p.label_ids, preds, average="macro")
    return {"accuracy": acc, "f1_macro": f1}


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """Configuration for the training run.

    Parameters
    ----------
    train_path : Path
        Path to the training JSONL file.
    valid_path : Path
        Path to the validation JSONL file.
    model_name : str
        HuggingFace model name or local path.
    num_epochs : int
        Number of training epochs.
    batch_size : int
        Batch size for training and evaluation.
    learning_rate : float
        Optimizer learning rate.
    max_length : int
        Maximum sequence length.
    wandb_project : str
        W&B project name.
    wandb_entity : str | None
        W&B entity (organisation/team) name.
    output_dir : Path
        Directory to save checkpoints and the final model.
    warmup_ratio : float
        Linear warmup ratio for learning rate.
    weight_decay : float
        Weight decay for the optimizer.
    """

    train_path: Path
    valid_path: Path
    model_name: str = "radlab/polish-cross-encoder"
    num_epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 2e-5
    max_length: int = 128
    wandb_project: str = "polar-twitteremo"
    wandb_entity: str | None = None
    output_dir: Path = field(default_factory=lambda: Path("output/polarity-model"))
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01


def run(cfg: ModelConfig) -> Path:
    """Run the full training loop using the HuggingFace Trainer.

    Parameters
    ----------
    cfg : ModelConfig
        Training configuration.

    Returns
    -------
    Path
        Path to the saved model directory.
    """
    # --- Tokenizer & datasets ---
    tokenizer = AutoTokenizer.from_pretrained(cfg.model_name)
    train_ds = _load_and_tokenize(cfg.train_path, tokenizer, cfg.max_length)
    valid_ds = _load_and_tokenize(cfg.valid_path, tokenizer, cfg.max_length)

    print(f"Train samples : {len(train_ds)}")
    print(f"Valid samples : {len(valid_ds)}")
    print(f"Model         : {cfg.model_name}")
    print(f"Epochs        : {cfg.num_epochs}")
    print(f"Batch size    : {cfg.batch_size}")
    print(f"LR            : {cfg.learning_rate}")
    print(f"W&B project   : {cfg.wandb_project}")
    print()

    # --- Model ---
    # The base model has num_labels=1 (binary), so we use ignore_mismatched_sizes=True
    # to load base weights and initialize a new 3-class classification head.
    model = AutoModelForSequenceClassification.from_pretrained(
        cfg.model_name,
        num_labels=NUM_LABELS,
        id2label=LABEL_MAP,
        label2id={v: k for k, v in LABEL_MAP.items()},
        ignore_mismatched_sizes=True,
    )

    # --- W&B trainer ---
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(cfg.output_dir),
            num_train_epochs=cfg.num_epochs,
            per_device_train_batch_size=cfg.batch_size,
            per_device_eval_batch_size=cfg.batch_size,
            learning_rate=cfg.learning_rate,
            warmup_ratio=cfg.warmup_ratio,
            weight_decay=cfg.weight_decay,
            logging_dir=str(cfg.output_dir / "logs"),
            logging_steps=min(100, max(1, len(train_ds) // cfg.batch_size)),
            eval_strategy="epoch",
            save_strategy="epoch",
            save_total_limit=2,
            load_best_model_at_end=True,
            metric_for_best_model="f1_macro",
            report_to=["wandb"],
            fp16=False,  # disabled to avoid CUDA issues on some setups
        ),
        train_dataset=train_ds,
        eval_dataset=valid_ds,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer, return_tensors="pt"),
        compute_metrics=_compute_metrics,
    )

    # --- Train ---
    train_result = trainer.train()

    # --- Log metrics ---
    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    eval_metrics = trainer.evaluate()
    trainer.log_metrics("eval", eval_metrics)
    trainer.save_metrics("eval", eval_metrics)

    # Final classification report per class
    pred_results = trainer.predict(valid_ds)
    preds = pred_results.predictions
    labels = pred_results.label_ids
    report = {}
    for cls_name in LABEL_NAMES:
        cls_idx = LABEL_NAMES.index(cls_name)
        cls_mask = labels == cls_idx
        if cls_mask.sum() > 0:
            cls_preds = np.argmax(preds, axis=1)[cls_mask]
            cls_true = labels[cls_mask]
            report[f"classification_report/{cls_name}"] = {
                "precision": float((cls_preds == cls_true).mean()),
                "recall": float((cls_preds == cls_true).mean()),
                "count": int(cls_mask.sum()),
            }
    wandb.log(report)
    wandb.finish()

    # --- Save best model ---
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(cfg.output_dir))
    tokenizer.save_pretrained(str(cfg.output_dir))
    best_f1 = eval_metrics.get("eval_f1_macro", 0.0)
    print(f"\nDone. Best model saved to: {cfg.output_dir} (eval_f1_macro={best_f1:.4f})")
    return cfg.output_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="train_polarity_model",
        description="Train a polarity classifier on twitteremo samples.",
    )
    parser.add_argument(
        "--train",
        type=Path,
        default=Path(
            "resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl"
        ),
        help="Path to the training JSONL file",
    )
    parser.add_argument(
        "--valid",
        type=Path,
        default=Path(
            "resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl"
        ),
        help="Path to the validation JSONL file",
    )
    parser.add_argument(
        "--base-model-path",
        default="radlab/polish-cross-encoder",
        help="Base model name or path for the cross-encoder (default: radlab/polish-cross-encoder)",
    )
    parser.add_argument(
        "--num-epochs",
        type=int,
        default=5,
        help="Number of training epochs (default: 5)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Training batch size (default: 32)",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
        help="Learning rate (default: 2e-5)",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=128,
        help="Max sequence length (default: 128)",
    )
    parser.add_argument(
        "--wandb-project",
        default="polar-twitteremo",
        help="Weights & Biases project name (default: polar-twitteremo)",
    )
    parser.add_argument(
        "--wandb-entity",
        default=None,
        help="Weights & Biases entity / team name",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/polarity-model"),
        help="Directory to save the trained model (default: output/polarity-model)",
    )
    args = parser.parse_args(argv)

    try:
        if not args.train.exists():
            print(f"Error: train file not found: {args.train}", file=sys.stderr)
            return 1
        if not args.valid.exists():
            print(f"Error: valid file not found: {args.valid}", file=sys.stderr)
            return 1

        cfg = ModelConfig(
            train_path=args.train,
            valid_path=args.valid,
            model_name=args.base_model_path,
            num_epochs=args.num_epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            max_length=args.max_length,
            wandb_project=args.wandb_project,
            wandb_entity=args.wandb_entity,
            output_dir=args.output_dir,
        )
        model_path = run(cfg)
        print(f"\nDone. Model saved to: {model_path}")

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
