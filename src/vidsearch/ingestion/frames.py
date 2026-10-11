"""Frame sampling interface; decoding backends can be plugged in later."""

from collections.abc import Iterator
from pathlib import Path


def sample_frames(
    video_path: str | Path, frames_per_second: float
) -> Iterator[tuple[float, bytes]]:
    """Yield timestamped encoded frames from a video."""
    if frames_per_second <= 0:
        raise ValueError("frames_per_second must be positive")
    raise NotImplementedError("configure an OpenCV or FFmpeg frame decoder")


def passes_motion_gate(
    previous: bytes | None, current: bytes, threshold: float
) -> bool:
    """Placeholder hook for a pixel-difference or optical-flow motion gate."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    if not current:
        raise ValueError("current frame must not be empty")
    raise NotImplementedError(
        "implement the motion metric for the selected frame decoder"
    )
