"""Safe local video-file discovery and loading."""

from dataclasses import dataclass
from pathlib import Path

from vidsearch.core.security import validate_local_path

VIDEO_SUFFIXES = frozenset({".mp4", ".mkv", ".mov", ".webm", ".avi"})


@dataclass(frozen=True, slots=True)
class VideoSource:
    path: Path
    name: str


def load_video(path: str | Path, allowed_root: str | Path) -> VideoSource:
    """Validate and describe a single local video file."""
    resolved = validate_local_path(path, allowed_root)
    if resolved.suffix.lower() not in VIDEO_SUFFIXES:
        raise ValueError(f"unsupported video file type: {resolved.suffix}")
    return VideoSource(path=resolved, name=resolved.name)


def discover_videos(
    directory: str | Path, allowed_root: str | Path
) -> list[VideoSource]:
    """List supported videos directly contained in a validated directory."""
    root = Path(allowed_root).expanduser().resolve(strict=True)
    candidate = Path(directory).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_dir():
        raise ValueError("directory must be inside the allowed media directory")
    return [
        VideoSource(path=item, name=item.name)
        for item in sorted(resolved.iterdir())
        if item.is_file() and item.suffix.lower() in VIDEO_SUFFIXES
    ]
