"""
Visualize the class distribution of negative/positive/neutral labels
in the twitteremo sample datasets.

Usage:

    python3 code/dataset/visualize_class_distribution.py \\
        --train resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \\
        --valid resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \\
        --output resources/dataset/twitteremo/class_distribution.png

"""

import sys
import json
import argparse
import matplotlib

from pathlib import Path

matplotlib.use("Agg")

import matplotlib.pyplot as plt


CLASSES = ["negatywny", "pozytywny", "neutralny"]
LABELS = {"negatywny": "Negatywny", "pozytywny": "Pozytywny", "neutralny": "Neutralny"}
COLORS = {"negatywny": "#d9534f", "pozytywny": "#5cb85c", "neutralny": "#f0ad4e"}


def _load_labels(path: Path) -> list[dict]:
    """
    Load class labels from a JSONL file.

    Parameters
    ----------
    path : Path
        Path to the JSONL file.

    Returns
    -------
    list[dict]
        List of dicts with class keys mapped to their label values.
    """
    labels: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            labels.append({cls: obj.get(cls, 0) for cls in CLASSES})
    return labels


def _count_distribution(labels: list[dict]) -> dict[str, int]:
    """
    Count occurrences of each class.

    Parameters
    ----------
    labels : list[dict]
        List of label dicts from ``_load_labels``.

    Returns
    -------
    dict[str, int]
        Mapping of class name to its count.
    """
    counts = {cls: 0 for cls in CLASSES}
    for label in labels:
        for cls in CLASSES:
            counts[cls] += label.get(cls, 0)
    return counts


def plot_distribution(
    train_counts: dict[str, int],
    valid_counts: dict[str, int],
    output_path: Path,
) -> Path:
    """
    Plot and save class distribution as a grouped bar chart.

    Parameters
    ----------
    train_counts : dict[str, int]
        Class counts for the train set.
    valid_counts : dict[str, int]
        Class counts for the validation set.
    output_path : Path
        Output PNG file path.

    Returns
    -------
    Path
        The output file path.
    """
    train_vals = [train_counts[c] for c in CLASSES]
    valid_vals = [valid_counts[c] for c in CLASSES]

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(CLASSES))
    width = 0.35

    bars_train = ax.bar(
        [i - width / 2 for i in x],
        train_vals,
        width,
        label="Train",
        alpha=0.85,
    )
    bars_valid = ax.bar(
        [i + width / 2 for i in x],
        valid_vals,
        width,
        label="Validation",
        alpha=0.85,
    )

    # Color each bar group individually
    for i, cls in enumerate(CLASSES):
        bars_train[i].set_color(COLORS[cls])
        bars_valid[i].set_color(COLORS[cls])
        bars_train[i].set_edgecolor("white")
        bars_valid[i].set_edgecolor("white")

    ax.set_xticks(list(x))
    ax.set_xticklabels([LABELS[c] for c in CLASSES], fontsize=11)
    ax.set_ylabel("Number of examples")
    ax.set_title(
        "Class distribution: negative / positive / neutral",
        fontsize=13,
        fontweight="bold",
    )
    ax.legend(loc="upper right")

    # Add value labels on bars
    for bars in (bars_train, bars_valid):
        for bar in bars:
            if bar.get_height() > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 20,
                    f"{int(bar.get_height())}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="semibold",
                )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="visualize_class_distribution",
        description="Visualize negative/positive/neutral class distribution.",
    )
    parser.add_argument(
        "--train",
        type=Path,
        default=Path("resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl"),
        help="Path to train JSONL file",
    )
    parser.add_argument(
        "--valid",
        type=Path,
        default=Path("resources/dataset/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl"),
        help="Path to validation JSONL file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("resources/dataset/twitteremo/class_distribution.png"),
        help="Output PNG image path",
    )
    args = parser.parse_args(argv)

    try:
        train_labels = _load_labels(args.train)
        valid_labels = _load_labels(args.valid)

        train_counts = _count_distribution(train_labels)
        valid_counts = _count_distribution(valid_labels)

        # Summary
        print("Class distribution:")
        print(f"{'Class':<12} {'Train':>8} {'Valid':>8}")
        for cls in CLASSES:
            print(f"{LABELS[cls]:<12} {train_counts[cls]:>8} {valid_counts[cls]:>8}")

        out = plot_distribution(train_counts, valid_counts, args.output)
        print(f"\nChart saved to: {out}")

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
