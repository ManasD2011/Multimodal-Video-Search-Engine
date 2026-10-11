"""Media metadata probing through the ffprobe executable."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from vidsearch.core.security import validate_file_size, validate_local_path


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    duration_seconds: float
    width: int | None
    height: int | None
    size_bytes: int


def probe_video(
    path: str | Path,
    allowed_root: str | Path,
    max_bytes: int,
    max_duration_seconds: float,
) -> VideoMetadata:
    """Probe a local file and enforce size and duration limits."""
    resolved = validate_local_path(path, allowed_root)
    size = validate_file_size(resolved.stat().st_size, max_bytes)
    process = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height",
            "-of",
            "json",
            str(resolved),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(process.stdout)
    duration = float(payload["format"]["duration"])
    if duration <= 0 or duration > max_duration_seconds:
        raise ValueError("video duration is outside the permitted range")
    video_stream: dict[str, object] = next(
        (
            stream
            for stream in payload.get("streams", [])
            if stream.get("codec_type") == "video"
        ),
        {},
    )
    width = video_stream.get("width")
    height = video_stream.get("height")
    return VideoMetadata(
        duration_seconds=duration,
        width=width if isinstance(width, int) else None,
        height=height if isinstance(height, int) else None,
        size_bytes=size,
    )
