"""
Application download_and_prepare_sample.

Fetches a dataset from HuggingFace Hub, randomly selects a given number of
examples, and writes them to a JSONL file.

Usage:

    python3 code/dataset/download_and_prepare_sample_twitteremo.py \\
        --dataset clarin-pl/twitteremo \\
        --num-samples 5000 \\
        --num-samples-valid 500 \\
        --output resources/dataset/twitteremo/clarinpl-twitteremo-train-sample-5k.jsonl \\
        --output-valid resources/dataset/twitteremo/twitteremo/clarinpl-twitteremo-valid-sample-500.jsonl \\
        --seed 42
"""

import sys
import json
import random
import argparse

from pathlib import Path
from datasets import load_dataset


def _write_jsonl(rows: list[dict], output_path: Path) -> Path:
    """Write a list of dicts to a JSONL file.

    Returns
    -------
    Path
        The output file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return output_path


def download_and_prepare_sample(
    dataset_name: str,
    split: str,
    num_samples: int,
    output_path: Path,
    seed: int | None = None,
) -> Path:
    """
    Fetch a dataset from HF, randomly select examples, and write to JSONL.

    Parameters
    ----------
    dataset_name : str
        Dataset name on HuggingFace Hub (e.g. ``clarin-pl/twitteremo``).
    split : str
        Split to load (e.g. ``train``, ``test``).
    num_samples : int
        Number of random examples to sample.
    output_path : Path
        Output JSONL file path.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    Path
        The output file path.

    Raises
    ------
    ValueError
        When ``num_samples`` exceeds the dataset size.
    """
    print(f"[1/3] Loading dataset '{dataset_name}' (split='{split}') ...")
    ds = load_dataset(dataset_name, split=split, trust_remote_code=True)

    total = len(ds)
    if num_samples > total:
        raise ValueError(
            f"Requested sample count ({num_samples}) exceeds "
            f"dataset size ({total})."
        )

    rng = random.Random(seed)
    indices = rng.sample(range(total), num_samples)
    subset = ds.select(indices)

    rows = list(subset)

    print(f"[2/3] Sampled {num_samples} examples out of {total}.")

    _write_jsonl(rows, output_path)

    print(f"[3/3] Written to '{output_path}'.")
    return output_path


def download_and_prepare_valid(
    dataset_name: str,
    split: str,
    num_samples: int,
    output_path: Path,
    used_indices: set[int],
    seed: int | None = None,
) -> Path:
    """
    Fetch a dataset and select examples for validation, excluding used indices.

    The ``used_indices`` parameter contains indices already sampled for train,
    so the validation set will be disjoint from train.

    Parameters
    ----------
    dataset_name : str
        Dataset name on HuggingFace Hub.
    split : str
        Split to load.
    num_samples : int
        Number of examples to sample for validation.
    output_path : Path
        Output JSONL file path.
    used_indices : set[int]
        Indices already taken by train. Validation will not overlap.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    Path
        The output file path.

    Raises
    ------
    ValueError
        When there are not enough unused indices available.
    """
    ds = load_dataset(dataset_name, split=split, trust_remote_code=True)
    total = len(ds)
    available = sorted(set(range(total)) - used_indices)

    if num_samples > len(available):
        raise ValueError(
            f"Requested validation count ({num_samples}) exceeds "
            f"available indices ({len(available)}); "
            f"after train ({len(used_indices)}) there are {len(available)} left."
        )

    rng = random.Random(seed)
    valid_indices = set(rng.sample(available, num_samples))
    subset = ds.select(list(valid_indices))

    rows = list(subset)

    print(f"[valid] Sampled {num_samples} examples out of {total} "
          f"({len(used_indices)} taken by train, {len(available)} available).")

    _write_jsonl(rows, output_path)
    print(f"[valid] Written to '{output_path}'.")
    return output_path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="download_and_prepare_sample",
        description=(
            "Fetch a dataset from HuggingFace Hub, randomly select "
            "examples, and write them to a JSONL file."
        ),
    )
    parser.add_argument(
        "--dataset",
        default="clarin-pl/twitteremo",
        help="HuggingFace dataset name (default: clarin-pl/twitteremo)",
    )
    parser.add_argument(
        "--split",
        default="train",
        help="Split to load (default: train)",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=100,
        help="Number of random examples for train (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("samples.jsonl"),
        help="Train output path (default: samples.jsonl)",
    )
    parser.add_argument(
        "--num-samples-valid",
        type=int,
        default=0,
        help="Number of random examples for validation -- disjoint set "
             "from train (default: 0 = no validation)",
    )
    parser.add_argument(
        "--output-valid",
        type=Path,
        default=Path("samples_valid.jsonl"),
        help="Validation output path (default: samples_valid.jsonl)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None)",
    )

    args = parser.parse_args(argv)

    try:
        download_and_prepare_sample(
            dataset_name=args.dataset,
            split=args.split,
            num_samples=args.num_samples,
            output_path=args.output,
            seed=args.seed,
        )

        if args.num_samples_valid > 0:
            rng = random.Random(args.seed)
            ds = load_dataset(
                args.dataset, split=args.split, trust_remote_code=True,
            )
            train_indices = set(rng.sample(range(len(ds)), args.num_samples))

            download_and_prepare_valid(
                dataset_name=args.dataset,
                split=args.split,
                num_samples=args.num_samples_valid,
                output_path=args.output_valid,
                used_indices=train_indices,
                seed=args.seed,
            )

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
