"""Reciprocal-rank fusion for merging independent result lists."""

from collections import defaultdict
from collections.abc import Sequence

from vidsearch.core.schemas import SearchHit


def reciprocal_rank_fusion(
    result_lists: Sequence[Sequence[SearchHit]], rank_constant: int = 60
) -> list[SearchHit]:
    """Fuse ranked lists by segment identity while preserving evidence."""
    if rank_constant < 1:
        raise ValueError("rank_constant must be positive")
    scores: dict[tuple[str, str, float, float], float] = defaultdict(float)
    hits: dict[tuple[str, str, float, float], SearchHit] = {}
    evidence: dict[tuple[str, str, float, float], list] = defaultdict(list)
    for result_list in result_lists:
        for rank, hit in enumerate(result_list, start=1):
            key = (
                hit.segment.video_id,
                hit.segment.segment_id,
                hit.segment.start_seconds,
                hit.segment.end_seconds,
            )
            scores[key] += 1.0 / (rank_constant + rank)
            hits[key] = hit
            evidence[key].extend(hit.evidence)
    return [
        SearchHit(
            segment=hits[key].segment,
            score=score,
            evidence=tuple(evidence[key]),
        )
        for key, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]
