"""Measure repeated command latency, throughput, and optional index size."""

from __future__ import annotations

import argparse
import json
import shlex
import statistics
import subprocess
import sys
import time
from pathlib import Path


def directory_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.exists():
        raise FileNotFoundError(f"index path does not exist: {path}")
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--command", required=True, help="Command to execute per measured run"
    )
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--queries-per-run", type=int, default=1)
    parser.add_argument("--index-path", type=Path)
    parser.add_argument(
        "--output", type=Path, default=Path("eval/results/performance.json")
    )
    args = parser.parse_args(argv)
    if args.runs < 1 or args.warmup < 0 or args.queries_per_run < 1:
        parser.error(
            "runs and queries-per-run must be positive; warmup cannot be negative"
        )

    command = shlex.split(args.command, posix=sys.platform != "win32")
    samples: list[float] = []
    try:
        for run_index in range(args.warmup + args.runs):
            started = time.perf_counter()
            subprocess.run(command, check=True)
            elapsed = time.perf_counter() - started
            if run_index >= args.warmup:
                samples.append(elapsed)
        total_seconds = sum(samples)
        report = {
            "command": command,
            "runs": len(samples),
            "warmup_runs": args.warmup,
            "queries_per_run": args.queries_per_run,
            "mean_latency_seconds": statistics.mean(samples),
            "median_latency_seconds": statistics.median(samples),
            "min_latency_seconds": min(samples),
            "max_latency_seconds": max(samples),
            "throughput_queries_per_second": (
                len(samples) * args.queries_per_run / total_seconds
                if total_seconds > 0
                else None
            ),
        }
        if args.index_path:
            report["index_size_bytes"] = directory_size(args.index_path)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"performance benchmark failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
