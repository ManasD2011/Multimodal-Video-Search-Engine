"""Compare retrieval ablations using prediction JSONL exports."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from eval.run_eval import evaluate_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument(
        "--predictions",
        action="append",
        required=True,
        metavar="NAME=PATH",
        help="Repeat for visual, visual_asr, visual_caption, visual_bm25, reranked, etc.",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("eval/results/ablations.csv")
    )
    parser.add_argument("--ks", type=int, nargs="+", default=[1, 5, 10])
    parser.add_argument("--iou-thresholds", type=float, nargs="+", default=[0.3, 0.5])
    args = parser.parse_args(argv)

    try:
        comparisons: list[tuple[str, dict[str, float | None]]] = []
        for item in args.predictions:
            name, separator, path = item.partition("=")
            if not separator or not name.strip() or not path.strip():
                raise ValueError(
                    f"invalid --predictions value {item!r}; expected NAME=PATH"
                )
            _, metrics = evaluate_files(
                args.ground_truth, Path(path), args.ks, args.iou_thresholds
            )
            comparisons.append((name.strip(), metrics))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["ablation", *comparisons[0][1].keys()]
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for name, metrics in comparisons:
                writer.writerow({"ablation": name, **metrics})
    except (OSError, ValueError, IndexError) as error:
        print(f"ablation evaluation failed: {error}", file=sys.stderr)
        return 1
    print(f"Ablation comparison written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
