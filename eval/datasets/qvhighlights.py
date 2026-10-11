"""Normalize QVHighlights-style temporal grounding annotations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def normalize_annotations(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Convert query rows with relevant_windows to canonical query records.

    Accepts canonical `relevant_windows` objects or common QVHighlights
    `relevant_windows` pairs of [start, end].
    """
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        query_id = str(row.get("query_id", row.get("qid", f"qvh-{index}")))
        query = str(row.get("query", "")).strip()
        video_id = str(row.get("video_id", row.get("vid", ""))).strip()
        if not query_id or not query or not video_id:
            raise ValueError(
                f"QVHighlights row {index} requires query, video ID, and query ID"
            )
        if query_id in seen:
            raise ValueError(f"duplicate query_id {query_id!r}")
        seen.add(query_id)
        source_windows = row.get("relevant_windows", [])
        if not isinstance(source_windows, list):
            raise ValueError(
                f"QVHighlights row {index} relevant_windows must be a list"
            )
        windows = [
            _normalize_window(window, video_id, index) for window in source_windows
        ]
        normalized.append(
            {
                "query_id": query_id,
                "query": query,
                "relevant_video_ids": [video_id],
                "relevant_windows": windows,
            }
        )
    return normalized


def _normalize_window(window: Any, video_id: str, row_index: int) -> dict[str, Any]:
    if isinstance(window, Mapping):
        start, end = window.get("start"), window.get("end")
        window_video_id = str(window.get("video_id", video_id))
    elif isinstance(window, (list, tuple)) and len(window) == 2:
        start, end = window
        window_video_id = video_id
    else:
        raise ValueError(f"QVHighlights row {row_index} has an invalid time window")
    start, end = float(start), float(end)
    if start < 0 or end <= start:
        raise ValueError(f"QVHighlights row {row_index} has invalid window bounds")
    return {"video_id": window_video_id, "start": start, "end": end}
