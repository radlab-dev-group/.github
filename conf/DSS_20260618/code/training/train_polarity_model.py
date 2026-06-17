"""
Train a polarity classification model (positive / negative / neutral)
on the twitteremo dataset samples using the HuggingFace Trainer API.

Usage:

    python3 code/training/train_polarity_model.py \\
        --train resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \\
        --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \\
        --base-model-path allegro/herbert-base-cased \\
        --wandb-project polar-twitteremo \\
        --output-dir /mnt/local/models/dss-2026-06/polarity-model/twitter-emo-sample-5k
"""

import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import numpy as np
import torch
import wandb
from datasets import Dataset as HFDataset
from matplotlib import pyplot as plt
from PIL import Image as PILImage
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EvalPrediction,
    TrainerCallback,
    TrainingArguments,
    Trainer,
    set_seed,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LABEL_MAP = {0: "neutralny", 1: "negatywny", 2: "pozytywny"}
LABEL_NAMES = list(LABEL_MAP.values())
NUM_LABELS = len(LABEL_NAMES)


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
    labels = p.label_ids

    # Global metrics
    acc = accuracy_score(labels, preds)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )

    metrics = {
        "accuracy": acc,
        "f1_macro": f1_macro,
        "precision_macro": precision_macro,
        "recall_macro": recall_macro,
    }

    # Per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, preds, average=None, labels=list(range(NUM_LABELS)), zero_division=0
    )

    for i, label_name in LABEL_MAP.items():
        metrics[f"f1_{label_name}"] = f1[i]
        metrics[f"precision_{label_name}"] = precision[i]
        metrics[f"recall_{label_name}"] = recall[i]
        metrics[f"support_{label_name}"] = int(support[i])

    return metrics


# ---------------------------------------------------------------------------
# W&B helpers
# ---------------------------------------------------------------------------


def _cm_heatmap_image(
    preds: np.ndarray, true_labels: np.ndarray, tag: str
) -> wandb.Image:
    """Render a confusion-matrix heatmap as a ``wandb.Image`` via matplotlib.

    Uses ``"viridis"`` colormap and a white figure background so the heatmap
    is clearly visible in W&B.
    """
    cm = confusion_matrix(true_labels, preds, labels=list(range(NUM_LABELS)))
    norm = plt.Normalize(vmin=0, vmax=cm.max() if cm.max() > 0 else 1)

    fig, ax = plt.subplots(figsize=(4, 3.5))
    fig.patch.set_facecolor("white")
    im = ax.imshow(cm, interpolation="nearest", cmap="viridis", norm=norm)
    ax.figure.colorbar(im, ax=ax, fraction=0.046)

    ax.set(
        xticks=list(range(NUM_LABELS)),
        xticklabels=LABEL_NAMES,
        yticks=list(range(NUM_LABELS)),
        yticklabels=LABEL_NAMES,
    )
    ax.set_ylabel("true label")
    ax.set_xlabel("predicted label")
    ax.set_title(f"Confusion matrix ({tag})")

    for i in range(NUM_LABELS):
        for j in range(NUM_LABELS):
            val = cm[i, j]
            ax.text(
                j,
                i,
                str(int(val)),
                ha="center",
                va="center",
                color="white" if norm(val) > 0.5 else "black",
            )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    pil_img = PILImage.open(buf)
    return wandb.Image(pil_img)


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
    p, n, ne = (
        obj.get("pozytywny", 0),
        obj.get("negatywny", 0),
        obj.get("neutralny", 0),
    )
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
    attention_mask = torch.stack(
        [torch.tensor(f["attention_mask"]) for f in features]
    )
    labels = torch.tensor([f["label"] for f in features])
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


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
    model_name: str = "allegro/herbert-base-cased"
    num_epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 1e-5
    max_length: int = 128
    wandb_project: str = "polar-twitteremo"
    wandb_entity: str | None = None
    output_dir: Path = field(default_factory=lambda: Path("output/polarity-model"))
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    seed: int = 42


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
    # --- Reproducibility ---
    set_seed(cfg.seed)

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

    # --- W&B (fully manual — no Trainer WandbCallback, no report_to) ---
    wandb.init(project=cfg.wandb_project, entity=cfg.wandb_entity)
    # Log config so project name / params are visible in W&B
    wandb.config.update(
        {
            "wandb_project": cfg.wandb_project,
            "wandb_entity": cfg.wandb_entity,
            "model_name": cfg.model_name,
            "num_epochs": cfg.num_epochs,
            "batch_size": cfg.batch_size,
            "learning_rate": cfg.learning_rate,
            "max_length": cfg.max_length,
            "warmup_ratio": cfg.warmup_ratio,
            "weight_decay": cfg.weight_decay,
        },
        allow_val_change=True,
    )

    # --- Callback that logs loss / eval / cm ---
    class _MetricsCallback(TrainerCallback):
        """Log training loss, eval metrics, and confusion-matrix heatmap."""

        def __init__(self):
            super().__init__()
            self._last_step = -1
            self._buffer = {}

        def _flush(self):
            if self._buffer and self._last_step >= 0:
                wandb.log(self._buffer, step=self._last_step)
                self._buffer = {}

        def on_log(self, args: TrainingArguments, state, control, **kwargs):
            logs = kwargs.get("logs")
            if not logs or not wandb.run:
                return

            if state.global_step != self._last_step:
                self._flush()
                self._last_step = state.global_step

            # Unify metric names to ensure history is correctly tracked in W&B
            for k, v in logs.items():
                if k.startswith("eval_"):
                    # Map eval_accuracy -> eval/accuracy
                    self._buffer[k.replace("eval_", "eval/")] = v
                elif k == "loss":
                    # Intermediate training loss
                    self._buffer["train/loss"] = v
                elif k == "train_loss":
                    # Final total loss - map to the same key as intermediate for a single curve
                    self._buffer["train/loss"] = v
                elif k == "learning_rate":
                    self._buffer["train/learning_rate"] = v
                elif k == "epoch":
                    self._buffer["train/epoch"] = v
                elif k.startswith("train_"):
                    # Other final metrics: train_runtime, train_samples_per_second, etc.
                    self._buffer[k.replace("train_", "train/")] = v
                else:
                    # Catch-all: prefix with train/ if not already prefixed
                    if "/" not in k:
                        self._buffer[f"train/{k}"] = v
                    else:
                        self._buffer[k] = v

        def on_evaluate(self, args, state, control, **kwargs):
            if not wandb.run:
                return

            if state.global_step != self._last_step:
                self._flush()
                self._last_step = state.global_step

            # Confusion matrix
            trainer = kwargs.get("trainer")
            if trainer is None or trainer.eval_dataset is None:
                return

            output = trainer.predict(trainer.eval_dataset)
            preds = np.argmax(output.predictions, axis=1)

            self._buffer["eval/confusion_matrix"] = _cm_heatmap_image(
                preds, output.label_ids, "eval"
            )

        def on_train_end(self, args, state, control, **kwargs):
            self._flush()

    # --- Trainer ---
    # report_to=[] disables the built-in WandbCallback (which would call
    # wandb.finish() and close the run before we can log our own metrics).
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
            gradient_accumulation_steps=2,
            max_grad_norm=1.0,
            lr_scheduler_type="cosine",
            adam_epsilon=1e-6,
            logging_dir=str(cfg.output_dir / "logs"),
            logging_steps=max(1, min(50, len(train_ds) // (cfg.batch_size * 10))),
            logging_first_step=True,
            eval_strategy="epoch",
            save_strategy="epoch",
            save_total_limit=2,
            load_best_model_at_end=True,
            metric_for_best_model="f1_macro",
            report_to=[],
            fp16=False,  # disabled to avoid CUDA issues on some setups
            seed=cfg.seed,
        ),
        train_dataset=train_ds,
        eval_dataset=valid_ds,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer, return_tensors="pt"),
        compute_metrics=_compute_metrics,
        callbacks=[_MetricsCallback()],
    )

    # --- Train ---
    train_result = trainer.train()

    # --- Eval + classification report on the best model ---
    # We disable the callback during the final manual evaluation to avoid
    # double logging or conflicting with the final manual wandb.log.
    trainer.pop_callback(_MetricsCallback)

    pred_results = trainer.predict(valid_ds)
    eval_metrics = pred_results.metrics

    # Use unified metric names consistent with the callback
    final_metrics = {}
    for k, v in eval_metrics.items():
        # Remove prefixes like 'test_' or 'eval_' and use 'eval/'
        new_key = k.replace("test_", "").replace("eval_", "")
        if "/" not in new_key:
            new_key = f"eval/{new_key}"
        final_metrics[new_key] = v

    # Add CM for best model
    preds = np.argmax(pred_results.predictions, axis=1)
    final_metrics["eval/confusion_matrix"] = _cm_heatmap_image(
        preds, pred_results.label_ids, "best_model"
    )

    wandb.log(final_metrics, step=train_result.global_step)

    # Log also a summary of final metrics for easy access
    wandb.run.summary.update(
        {
            "final_accuracy": eval_metrics.get(
                "test_accuracy", eval_metrics.get("accuracy")
            ),
            "final_f1_macro": eval_metrics.get(
                "test_f1_macro", eval_metrics.get("f1_macro")
            ),
        }
    )

    wandb.finish()

    # --- Save best model ---
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(cfg.output_dir))
    tokenizer.save_pretrained(str(cfg.output_dir))
    best_f1 = eval_metrics.get("test_f1_macro", eval_metrics.get("f1_macro", 0.0))
    print(
        f"\nDone. Best model saved to: {cfg.output_dir} "
        f"(eval_f1_macro={best_f1:.4f})"
    )
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
        default="allegro/herbert-base-cased",
        help="Base model name or path for the cross-encoder (default: allegro/herbert-base-cased)",
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
        default=1e-5,
        help="Learning rate (default: 1e-5)",
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
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
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
            seed=args.seed,
        )
        model_path = run(cfg)
        print(f"\nDone. Model saved to: {model_path}")

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
