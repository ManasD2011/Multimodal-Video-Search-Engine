"""Pure-Python time-window segmentation helpers."""

from vidsearch.core.schemas import Segment


def fixed_windows(
    video_id: str, duration_seconds: float, window_seconds: float
) -> list[Segment]:
    """Split a video duration into contiguous windows, including a short tail."""
    if not video_id.strip() or duration_seconds <= 0 or window_seconds <= 0:
        raise ValueError("video id, duration, and window size must be positive")
    segments: list[Segment] = []
    start = 0.0
    while start < duration_seconds:
        end = min(start + window_seconds, duration_seconds)
        segments.append(
            Segment(
                video_id=video_id,
                start_seconds=start,
                end_seconds=end,
                segment_id=f"{video_id}:{len(segments)}",
            )
        )
        start = end
    return segments


def merge_adjacent(
    segments: list[Segment], max_gap_seconds: float = 0.0
) -> list[Segment]:
    """Merge overlapping or near-adjacent segments from the same video."""
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be non-negative")
    ordered = sorted(segments, key=lambda item: (item.video_id, item.start_seconds))
    merged: list[Segment] = []
    for current in ordered:
        if (
            merged
            and merged[-1].video_id == current.video_id
            and current.start_seconds <= merged[-1].end_seconds + max_gap_seconds
        ):
            previous = merged[-1]
            merged[-1] = Segment(
                video_id=previous.video_id,
                start_seconds=previous.start_seconds,
                end_seconds=max(previous.end_seconds, current.end_seconds),
                segment_id=previous.segment_id,
            )
        else:
            merged.append(current)
    return merged


def detect_scenes(video_path: str) -> list[float]:
    """Return scene-boundary timestamps from a configured scene detector."""
    raise NotImplementedError("configure a scene detection backend")
