"""Validated URL entry point for a future yt-dlp-backed downloader."""

from vidsearch.core.security import validate_public_url


def validate_download_url(url: str) -> str:
    """Validate a remote media URL before passing it to a downloader."""
    return validate_public_url(url)


def download_video(url: str, destination: str) -> None:
    """Download integration is intentionally not enabled in the initial scaffold."""
    validate_download_url(url)
    if not destination.strip():
        raise ValueError("destination must not be empty")
    raise NotImplementedError("connect a sandboxed yt-dlp adapter before downloading")
