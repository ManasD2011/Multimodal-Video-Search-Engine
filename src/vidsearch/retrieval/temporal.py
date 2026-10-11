"""Temporal grouping helpers for nearby matches."""

from vidsearch.core.schemas import SearchHit, Segment


def merge_adjacent_hits(
    hits: list[SearchHit], max_gap_seconds: float = 0.0
) -> list[SearchHit]:
    """Merge overlapping/nearby hits from the same video, retaining best score."""
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be non-negative")
    ordered = sorted(
        hits, key=lambda hit: (hit.segment.video_id, hit.segment.start_seconds)
    )
    merged: list[SearchHit] = []
    for hit in ordered:
        if (
            merged
            and merged[-1].segment.video_id == hit.segment.video_id
            and hit.segment.start_seconds
            <= merged[-1].segment.end_seconds + max_gap_seconds
        ):
            previous = merged[-1]
            segment = Segment(
                video_id=previous.segment.video_id,
                start_seconds=previous.segment.start_seconds,
                end_seconds=max(previous.segment.end_seconds, hit.segment.end_seconds),
                segment_id=previous.segment.segment_id,
            )
            merged[-1] = SearchHit(
                segment=segment,
                score=max(previous.score, hit.score),
                evidence=previous.evidence + hit.evidence,
            )
        else:
            merged.append(hit)
    return sorted(merged, key=lambda hit: hit.score, reverse=True)


def select_temporal_result(
    hits: list[SearchHit], mode: str = "best"
) -> list[SearchHit]:
    """Choose all results, the earliest match, or the highest-scoring match."""
    if mode == "all":
        return list(hits)
    if mode == "earliest":
        return sorted(hits, key=lambda hit: (hit.segment.start_seconds, -hit.score))[:1]
    if mode == "best":
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:1]
    raise ValueError("mode must be one of: all, earliest, best")
