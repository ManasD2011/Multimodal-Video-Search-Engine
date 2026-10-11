"""Audio extraction and voice-activity-detection interfaces."""

from pathlib import Path


def extract_audio(video_path: str | Path, output_path: str | Path) -> Path:
    """Extract mono audio using the configured FFmpeg adapter."""
    raise NotImplementedError("configure an FFmpeg audio extraction adapter")


def detect_speech(audio_path: str | Path) -> list[tuple[float, float]]:
    """Return speech intervals as ``(start_seconds, end_seconds)`` pairs."""
    raise NotImplementedError("configure a voice activity detection backend")
