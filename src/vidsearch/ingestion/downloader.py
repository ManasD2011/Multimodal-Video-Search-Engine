"""Safe, YouTube-only video download integration for local development."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from vidsearch.core.security import ALLOWED_VIDEO_SUFFIXES, validate_public_url

YOUTUBE_HOSTS = frozenset(
    {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}
)


class DownloaderUnavailable(RuntimeError):
    """Raised when the optional yt-dlp dependency is not installed."""


class VideoDownloadError(RuntimeError):
    """Raised when a YouTube video cannot be downloaded under local limits."""


@dataclass(frozen=True, slots=True)
class DownloadedVideo:
    path: Path
    filename: str
    duration_seconds: float


def validate_download_url(url: str) -> str:
    """Accept only public HTTPS YouTube URLs, never arbitrary network targets."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in YOUTUBE_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in {None, 443}
    ):
        raise ValueError("only public HTTPS YouTube video URLs are supported")
    return validate_public_url(url)


def _safe_filename(title: object, video_id: object, suffix: str) -> str:
    source = str(title or video_id or "youtube-video")
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", source).strip(" .")
    return f"{(safe or 'youtube-video')[:150]}{suffix}"


def download_video(
    url: str,
    destination: str | Path,
    max_bytes: int,
    max_duration_seconds: int,
) -> DownloadedVideo:
    """Download one permitted YouTube video into an empty temporary directory."""
    validated_url = validate_download_url(url)
    output_dir = Path(destination).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise ValueError("download destination must be an empty directory")

    try:
        import yt_dlp
    except ImportError as error:
        raise DownloaderUnavailable(
            "YouTube imports require the optional dependencies; run "
            '"python -m pip install -e .[search]".'
        ) from error

    def check_video(info: dict[str, object], *, incomplete: bool = False) -> str | None:
        del incomplete
        duration = info.get("duration")
        if not isinstance(duration, (int, float)) or duration <= 0:
            return "video duration is unavailable"
        if duration > max_duration_seconds:
            return f"video exceeds the {max_duration_seconds}-second duration limit"
        size = info.get("filesize") or info.get("filesize_approx")
        if isinstance(size, (int, float)) and size > max_bytes:
            return f"video exceeds the {max_bytes}-byte size limit"
        return None

    options: dict[str, object] = {
        "format": "best[ext=mp4]/best",
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "max_filesize": max_bytes,
        "merge_output_format": "mp4",
        "match_filter": check_video,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(validated_url, download=True)
    except yt_dlp.utils.DownloadError as error:
        raise VideoDownloadError(
            "YouTube could not download this video. Check the URL, availability, "
            "and configured size or duration limits."
        ) from error

    if not isinstance(info, dict):
        raise VideoDownloadError("YouTube returned no video metadata")
    duration = info.get("duration")
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise VideoDownloadError("YouTube video duration is unavailable")
    if duration > max_duration_seconds:
        raise VideoDownloadError(
            f"video exceeds the {max_duration_seconds}-second duration limit"
        )

    files = [
        path
        for path in output_dir.iterdir()
        if path.is_file() and path.suffix.lower() in ALLOWED_VIDEO_SUFFIXES
    ]
    if len(files) != 1:
        raise VideoDownloadError("YouTube did not produce one supported video file")
    media_path = files[0].resolve()
    if not media_path.is_relative_to(output_dir):
        raise VideoDownloadError("downloaded file escaped its temporary directory")
    size_bytes = media_path.stat().st_size
    if size_bytes < 1 or size_bytes > max_bytes:
        raise VideoDownloadError(f"downloaded video exceeds the {max_bytes}-byte limit")
    return DownloadedVideo(
        path=media_path,
        filename=_safe_filename(info.get("title"), info.get("id"), media_path.suffix),
        duration_seconds=float(duration),
    )
