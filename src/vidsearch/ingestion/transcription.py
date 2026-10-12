"""CPU speech transcription used to create searchable video evidence."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import isfinite
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TranscriptChunk:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True, slots=True)
class Transcription:
    duration_seconds: float
    chunks: tuple[TranscriptChunk, ...]


@lru_cache(maxsize=2)
def _load_model(model_name: str, cache_dir: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise RuntimeError(
            "Speech indexing requires the optional dependencies; run "
            '"python -m pip install -e .[search]".'
        ) from error
    return WhisperModel(
        model_name,
        device="cpu",
        compute_type="int8",
        download_root=cache_dir,
    )


def transcribe_video(
    video_path: Path, model_cache_dir: Path, model_name: str = "base"
) -> Transcription:
    """Transcribe speech locally with Faster-Whisper's CPU/INT8 model."""
    model_cache_dir.mkdir(parents=True, exist_ok=True)
    model = _load_model(model_name, str(model_cache_dir.resolve()))
    segments, info = model.transcribe(str(video_path), vad_filter=True)
    duration = float(info.duration)
    if not isfinite(duration) or duration <= 0:
        raise ValueError("could not determine video duration")
    chunks = tuple(
        TranscriptChunk(
            start_seconds=float(segment.start),
            end_seconds=float(segment.end),
            text=segment.text.strip(),
        )
        for segment in segments
        if segment.text.strip()
    )
    return Transcription(duration_seconds=duration, chunks=chunks)
