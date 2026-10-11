# Evaluation

Evaluation is separate from correctness tests. The tools under `eval/` consume
canonical JSONL annotations and ranked prediction exports, so a prediction
adapter can be measured without coupling evaluation to the unfinished API.

The repository includes metric, ablation, dataset-normalization, and
performance scripts. The checked-in custom query is synthetic example data;
there are no committed benchmark claims or representative production results.

## Input data

Ground-truth JSONL uses one object per query:

```json
{"query_id":"q1","query":"a person opens a door","relevant_video_ids":["video-1"],"relevant_windows":[{"video_id":"video-1","start":2.0,"end":5.5}]}
```

Prediction JSONL uses one object per query with results ordered from highest
to lowest relevance:

```json
{"query_id":"q1","results":[{"video_id":"video-1","start":2.4,"end":5.0,"score":0.91}]}
```

Times are seconds from the beginning of the video. Every prediction query ID
must exist in the ground truth. A ground-truth query without a prediction is
scored as an empty result list.

## Metrics

- `Recall@k`: whether any of the first *k* results matches a relevant video or
  reaches the configured temporal IoU threshold.
- `MRR`: reciprocal rank of the first relevant video or temporal result.
- `MeanIoU`: best temporal IoU of the rank-one result, averaged over queries
  that have temporal labels.
- `R@1@IoU`: whether the rank-one temporal result reaches each configured IoU
  threshold.

When a query has relevant windows, temporal overlap determines relevance;
otherwise, relevant video IDs are used. `Recall@k` and `MRR` use the default
IoU threshold of 0.5 for temporal annotations. Configured `iou_thresholds`
apply to the separate `R@1@IoU` metrics. Video-level annotations cannot
support temporal IoU metrics.

## Running evaluation

```powershell
python -m eval.run_eval --ground-truth eval/datasets/custom/queries.jsonl --predictions data/predictions.jsonl --output-dir eval/results
```

The command writes per-query CSV, aggregate CSV, and a Markdown summary.
Alternatively, pass a JSON configuration file with ground-truth and
prediction paths, `ks`, `iou_thresholds`, and `output_dir`:

```powershell
python -m eval.run_eval --config eval-config.json
```

## Ablations

Compare named prediction exports on the same annotation set:

```powershell
python -m eval.ablations --ground-truth eval/datasets/custom/queries.jsonl --predictions visual=data/visual.jsonl --predictions visual_asr=data/visual_asr.jsonl --output eval/results/ablations.csv
```

The ablation tool evaluates the supplied exports; it does not run or configure
the model combinations itself. Use consistent query sets, model versions,
preprocessing, and ranking limits for each export.

## Performance benchmark

`eval.benchmark_perf` runs a command repeatedly and reports mean, median,
minimum, and maximum latency, configured query throughput, and optional index
size:

```powershell
python -m eval.benchmark_perf --command "python -m your_adapter" --runs 10 --warmup 1 --queries-per-run 100 --index-path data/index --output eval/results/performance.json
```

The command being measured is responsible for producing its own prediction or
index artifacts. Record hardware, dataset revision, warm-up policy, model
versions, and configuration with each benchmark for reproducibility.

## Dataset and result policy

The MSR-VTT and QVHighlights adapters normalize user-provided annotations;
they do not download datasets. Document dataset source, licence, attribution,
revision, and any annotation changes in
[`eval/datasets/custom/README.md`](../eval/datasets/custom/README.md). Do not
commit raw videos or downloaded benchmark archives. Store generated result
tables under `eval/results/` and include enough run metadata to reproduce the
numbers.
