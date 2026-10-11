"""Normalize MSR-VTT-style video-caption annotations to video-level queries."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def normalize_captions(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Convert rows with video_id/caption fields to canonical query records.

    Rows sharing a video ID are grouped as alternate text queries, each with
    that video's ID as its video-level relevance label. Timestamps are not
    inferred because MSR-VTT caption annotations are video-level.
    """
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        video_id = str(row.get("video_id", row.get("video", ""))).strip()
        query = str(row.get("caption", row.get("sentence", ""))).strip()
        if not video_id or not query:
            raise ValueError(f"MSR-VTT row {index} requires video_id and caption")
        query_id = str(row.get("query_id", f"msrvtt-{index}"))
        if query_id in seen:
            raise ValueError(f"duplicate query_id {query_id!r}")
        seen.add(query_id)
        normalized.append(
            {
                "query_id": query_id,
                "query": query,
                "relevant_video_ids": [video_id],
                "relevant_windows": [],
            }
        )
    return normalized
