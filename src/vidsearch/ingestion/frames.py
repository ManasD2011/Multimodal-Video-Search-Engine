"""Timestamped frame sampling for visual video search."""

from collections.abc import Iterator
from pathlib import Path


def sample_frames(
    video_path: str | Path, frames_per_second: float
) -> Iterator[tuple[float, bytes]]:
    """Yield timestamped JPEG frames at a bounded sampling rate."""
    if frames_per_second <= 0:
        raise ValueError("frames_per_second must be positive")
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError(
            "Visual search requires OpenCV. Install it with "
            '`python -m pip install -e ".[visual]`.'
        ) from error

    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(f"video file not found: {path}")

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        capture.release()
        raise ValueError("video could not be opened for frame extraction")

    try:
        source_fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / source_fps if source_fps > 0 else 0
        if duration <= 0:
            raise ValueError("video duration could not be determined for frame search")

        interval = 1.0 / frames_per_second
        timestamp = 0.0
        while timestamp < duration:
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            success, frame = capture.read()
            if not success:
                break
            encoded, image = cv2.imencode(".jpg", frame)
            if not encoded:
                raise ValueError(f"frame at {timestamp:.2f}s could not be encoded")
            yield timestamp, image.tobytes()
            timestamp += interval
    finally:
        capture.release()


def passes_motion_gate(
    previous: bytes | None, current: bytes, threshold: float
) -> bool:
    """Placeholder hook for an optional pixel-difference motion gate."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    if not current:
        raise ValueError("current frame must not be empty")
    raise NotImplementedError("motion gating is not configured")
