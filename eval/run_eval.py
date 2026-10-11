"""Evaluate ranked JSONL predictions against canonical JSONL annotations."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from eval.metrics import evaluate_query


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid JSON: {error.msg}"
                ) from error
            if not isinstance(value, dict):
                raise ValueError(
                    f"{path}:{line_number}: each JSONL record must be an object"
                )
            records.append(value)
    return records


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        value = json.loads(text)
    else:
        try:
            import yaml
        except ImportError as error:
            raise ValueError(
                "YAML config requires PyYAML; use JSON or install PyYAML"
            ) from error
        value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ValueError("evaluation config must contain an object/mapping")
    return value


def evaluate_files(
    ground_truth_path: Path,
    predictions_path: Path,
    ks: list[int],
    iou_thresholds: list[float],
) -> tuple[list[dict[str, Any]], dict[str, float | None]]:
    annotations = read_jsonl(ground_truth_path)
    predictions = read_jsonl(predictions_path)
    annotations_by_id = _unique_by_query_id(annotations, "ground truth")
    predictions_by_id = _unique_by_query_id(predictions, "predictions")
    unknown_ids = predictions_by_id.keys() - annotations_by_id.keys()
    if unknown_ids:
        raise ValueError(
            f"prediction query IDs absent from ground truth: {sorted(unknown_ids)}"
        )

    per_query: list[dict[str, Any]] = []
    for query_id, annotation in annotations_by_id.items():
        prediction = predictions_by_id.get(
            query_id, {"query_id": query_id, "results": []}
        )
        per_query.append(evaluate_query(prediction, annotation, ks, iou_thresholds))
    return per_query, aggregate_metrics(per_query)


def aggregate_metrics(
    rows: list[dict[str, Any]],
) -> dict[str, float | None]:
    if not rows:
        raise ValueError("ground truth contains no query records")
    names = [name for name in rows[0] if name != "query_id"]
    aggregate: dict[str, float | None] = {}
    for name in names:
        values = [float(row[name]) for row in rows if row.get(name) is not None]
        aggregate[name] = sum(values) / len(values) if values else None
    return aggregate


def _unique_by_query_id(
    records: list[dict[str, Any]], label: str
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if "query_id" not in record:
            raise ValueError(f"{label} record is missing query_id")
        query_id = str(record["query_id"])
        if query_id in indexed:
            raise ValueError(f"{label} contains duplicate query_id {query_id!r}")
        indexed[query_id] = record
    return indexed


def write_outputs(
    per_query: list[dict[str, Any]],
    aggregate: dict[str, float | None],
    output_dir: Path,
    run_name: str = "evaluation",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    per_query_path = output_dir / f"{run_name}_per_query.csv"
    with per_query_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_query[0]))
        writer.writeheader()
        writer.writerows(per_query)

    aggregate_path = output_dir / f"{run_name}_metrics.csv"
    with aggregate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerows(aggregate.items())

    report_path = output_dir / f"{run_name}.md"
    with report_path.open("w", encoding="utf-8") as handle:
        handle.write(f"# Evaluation: {run_name}\n\n")
        handle.write("| Metric | Value |\n|---|---:|\n")
        for name, value in aggregate.items():
            rendered = "N/A" if value is None else f"{value:.4f}"
            handle.write(f"| {name} | {rendered} |\n")
        handle.write(f"\nQueries evaluated: {len(per_query)}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="JSON or YAML evaluation config")
    parser.add_argument("--ground-truth", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("eval/results"))
    parser.add_argument("--run-name", default="evaluation")
    parser.add_argument("--ks", type=int, nargs="+")
    parser.add_argument("--iou-thresholds", type=float, nargs="+")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config) if args.config else {}
        ground_truth = args.ground_truth or _config_path(
            config, "ground_truth", args.config
        )
        predictions = args.predictions or _config_path(
            config, "predictions", args.config
        )
        if ground_truth is None or predictions is None:
            parser.error(
                "provide --ground-truth and --predictions, or both in --config"
            )
        ks = args.ks or config.get("ks", [1, 5, 10])
        thresholds = args.iou_thresholds or config.get("iou_thresholds", [0.3, 0.5])
        output_dir = args.output_dir
        if args.output_dir == Path("eval/results") and config.get("output_dir"):
            output_dir = _resolve_path(config["output_dir"], args.config)
        per_query, aggregate = evaluate_files(ground_truth, predictions, ks, thresholds)
        write_outputs(per_query, aggregate, output_dir, args.run_name)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"evaluation failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(aggregate, indent=2))
    print(f"Results written to {output_dir.resolve()}")
    return 0


def _config_path(
    config: dict[str, Any], key: str, config_path: Path | None
) -> Path | None:
    value = config.get(key)
    return _resolve_path(value, config_path) if value is not None else None


def _resolve_path(value: str | Path, config_path: Path | None) -> Path:
    path = Path(value)
    if not path.is_absolute() and config_path is not None:
        return (config_path.parent / path).resolve()
    return path


if __name__ == "__main__":
    raise SystemExit(main())
