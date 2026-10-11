"""Metrics for video retrieval and temporal moment localization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def temporal_iou(
    predicted: Mapping[str, Any], ground_truth: Mapping[str, Any]
) -> float:
    """Compute temporal intersection-over-union for two second-based windows."""
    p_start, p_end = _window(predicted)
    g_start, g_end = _window(ground_truth)
    intersection = max(0.0, min(p_end, g_end) - max(p_start, g_start))
    union = max(p_end, g_end) - min(p_start, g_start)
    return intersection / union if union > 0 else 0.0


def recall_at_k(
    results: Sequence[Mapping[str, Any]],
    relevant_video_ids: Sequence[str] = (),
    relevant_windows: Sequence[Mapping[str, Any]] = (),
    k: int = 10,
    iou_threshold: float = 0.5,
) -> float:
    """Return whether any of the first k results matches a relevant item."""
    if k < 1:
        raise ValueError("k must be at least 1")
    if relevant_windows:
        return float(
            any(
                _matches_window(item, relevant_windows, iou_threshold)
                for item in results[:k]
            )
        )
    if relevant_video_ids:
        relevant = set(relevant_video_ids)
        return float(any(item.get("video_id") in relevant for item in results[:k]))
    return 0.0


def reciprocal_rank(
    results: Sequence[Mapping[str, Any]],
    relevant_video_ids: Sequence[str] = (),
    relevant_windows: Sequence[Mapping[str, Any]] = (),
    iou_threshold: float = 0.5,
) -> float:
    """Return the reciprocal rank of the first relevant result, or zero."""
    relevant = set(relevant_video_ids)
    for rank, item in enumerate(results, start=1):
        is_relevant = (
            _matches_window(item, relevant_windows, iou_threshold)
            if relevant_windows
            else item.get("video_id") in relevant
        )
        if is_relevant:
            return 1.0 / rank
    return 0.0


def mean_iou_at_1(
    results: Sequence[Mapping[str, Any]],
    relevant_windows: Sequence[Mapping[str, Any]],
) -> float | None:
    """Return best rank-1 temporal IoU; None when labels have no windows."""
    if not relevant_windows:
        return None
    if not results:
        return 0.0
    return _best_window_iou(results[0], relevant_windows)


def recall_at_1_iou(
    results: Sequence[Mapping[str, Any]],
    relevant_windows: Sequence[Mapping[str, Any]],
    iou_threshold: float,
) -> float | None:
    """Return rank-1 temporal success at an IoU threshold."""
    _validate_threshold(iou_threshold)
    if not relevant_windows:
        return None
    return float(
        bool(results) and _matches_window(results[0], relevant_windows, iou_threshold)
    )


def evaluate_query(
    prediction: Mapping[str, Any],
    annotation: Mapping[str, Any],
    ks: Sequence[int] = (1, 5, 10),
    iou_thresholds: Sequence[float] = (0.3, 0.5),
) -> dict[str, float | None | str]:
    """Compute configured metrics for one query."""
    results = prediction.get("results", [])
    if not isinstance(results, list):
        raise ValueError("prediction 'results' must be a list")
    video_ids = annotation.get("relevant_video_ids", [])
    windows = annotation.get("relevant_windows", [])
    if not isinstance(video_ids, list) or not isinstance(windows, list):
        raise ValueError("relevant_video_ids and relevant_windows must be lists")

    metrics: dict[str, float | None | str] = {
        "query_id": str(annotation["query_id"]),
        "MRR": reciprocal_rank(results, video_ids, windows),
        "MeanIoU": mean_iou_at_1(results, windows),
    }
    for k in ks:
        metrics[f"Recall@{k}"] = recall_at_k(results, video_ids, windows, k=k)
    for threshold in iou_thresholds:
        metrics[f"R@1@IoU{threshold:g}"] = recall_at_1_iou(results, windows, threshold)
    return metrics


def _matches_window(
    prediction: Mapping[str, Any],
    relevant_windows: Sequence[Mapping[str, Any]],
    iou_threshold: float,
) -> bool:
    _validate_threshold(iou_threshold)
    return _best_window_iou(prediction, relevant_windows) >= iou_threshold


def _best_window_iou(
    prediction: Mapping[str, Any],
    relevant_windows: Sequence[Mapping[str, Any]],
) -> float:
    try:
        predicted_start, predicted_end = _window(prediction)
    except (KeyError, TypeError, ValueError):
        return 0.0
    best_iou = 0.0
    for target in relevant_windows:
        if prediction.get("video_id") != target.get("video_id"):
            continue
        try:
            target_start, target_end = _window(target)
        except (KeyError, TypeError, ValueError):
            continue
        intersection = max(
            0.0, min(predicted_end, target_end) - max(predicted_start, target_start)
        )
        union = max(predicted_end, target_end) - min(predicted_start, target_start)
        if union > 0:
            best_iou = max(best_iou, intersection / union)
    return best_iou


def _window(item: Mapping[str, Any]) -> tuple[float, float]:
    start, end = float(item["start"]), float(item["end"])
    if start < 0 or end <= start:
        raise ValueError("temporal windows require 0 <= start < end")
    return start, end


def _validate_threshold(threshold: float) -> None:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("IoU threshold must be between 0 and 1")
