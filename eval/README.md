# Evaluation

The evaluation tools are deliberately independent of the application runtime.
They consume canonical JSONL query annotations and ranked search results, so
an engine adapter can export results without coupling benchmark code to an
unfinished API.

## Canonical input formats

Ground-truth JSONL has one record per query:

```json
{"query_id":"q1","query":"a person opens a door","relevant_video_ids":["video-1"],"relevant_windows":[{"video_id":"video-1","start":2.0,"end":5.5}]}
```

`relevant_video_ids` supports video-level benchmarks such as MSR-VTT.
`relevant_windows` contains zero or more timestamped relevant intervals and
supports temporal benchmarks such as QVHighlights. Times are seconds from the
start of the video.

Prediction JSONL has one record per query, with results in descending
relevance order:

```json
{"query_id":"q1","results":[{"video_id":"video-1","start":2.4,"end":5.0,"score":0.91}]}
```

The first result is rank 1. `start` and `end` may be omitted for video-level
results. Every prediction query ID must exist in ground truth; missing results
are treated as an empty ranked list.

## Run evaluation

```powershell
python -m eval.run_eval --ground-truth path\to\queries.jsonl --predictions path\to\predictions.jsonl --output-dir eval\results
```

Or pass a JSON configuration file (a YAML file is also supported when
PyYAML is installed):

```json
{
  "ground_truth": "eval/datasets/custom/queries.jsonl",
  "predictions": "data/predictions.jsonl",
  "ks": [1, 5, 10],
  "iou_thresholds": [0.3, 0.5],
  "output_dir": "eval/results"
}
```

```powershell
python -m eval.run_eval --config eval-config.json
```

The run writes a per-query metrics CSV, an aggregate metrics CSV, and a
Markdown summary. `Recall@k` and `MRR` use video-ID relevance when a query has
video-level labels; otherwise they use temporal overlap at the configured
default IoU threshold. `MeanIoU` averages the best temporal IoU of the rank-1
prediction across queries with timestamp labels. `R@1@IoU` is reported for
each configured IoU threshold.

## Dataset adapters

- `datasets/msrvtt.py` normalizes MSR-VTT-style caption rows into
  video-level query annotations. Because those annotations do not provide
  timestamps, they are not suitable for temporal-IoU metrics.
- `datasets/qvhighlights.py` normalizes QVHighlights-style query annotations
  and relevant windows into the canonical format.
- `datasets/custom/queries.jsonl` is a small synthetic example. Replace or
  extend it with appropriately licensed annotations; do not commit downloaded
  raw datasets or video files.

Dataset-specific source licences and attribution belong in
`datasets/custom/README.md`. The adapters only normalize annotation files
provided by the user; they do not download benchmark data.

## Ablations and performance

`python -m eval.ablations --ground-truth ... --predictions visual=... --predictions visual_asr=...`
evaluates multiple prediction exports against the same labels.
`python -m eval.benchmark_perf --command "python -m your_adapter" --runs 10`
measures end-to-end command latency and throughput. The benchmark command
must emit its output/index artifacts itself; pass `--index-path` to report
their size.

Results are reproducible only when the prediction-generation adapter records
its model versions, configuration, random seed, and dataset revision. Keep
those details with the result files or in the benchmark run metadata.
