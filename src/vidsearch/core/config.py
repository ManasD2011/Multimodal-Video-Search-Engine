"""Application settings with conservative environment-variable defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path = Path("data")
    max_video_bytes: int = 2_000_000_000
    max_video_duration_seconds: int = 3_600
    frame_rate: float = 1.0
    segment_seconds: float = 10.0
    retrieval_top_k: int = 20
    qdrant_url: str = "http://localhost:6333"
    database_url: str = "sqlite:///data/vidsearch.db"

    def __post_init__(self) -> None:
        if self.max_video_bytes <= 0 or self.max_video_duration_seconds <= 0:
            raise ValueError("video limits must be positive")
        if self.frame_rate <= 0 or self.segment_seconds <= 0:
            raise ValueError("frame rate and segment duration must be positive")
        if self.retrieval_top_k < 1:
            raise ValueError("retrieval_top_k must be positive")

    @classmethod
    def from_env(cls) -> Settings:
        """Load supported settings from the process environment."""
        return cls(
            data_dir=Path(os.getenv("VIDSEARCH_DATA_DIR", "data")),
            max_video_bytes=int(os.getenv("VIDSEARCH_MAX_VIDEO_BYTES", "2000000000")),
            max_video_duration_seconds=int(
                os.getenv("VIDSEARCH_MAX_VIDEO_DURATION_SECONDS", "3600")
            ),
            frame_rate=float(os.getenv("VIDSEARCH_FRAME_RATE", "1")),
            segment_seconds=float(os.getenv("VIDSEARCH_SEGMENT_SECONDS", "10")),
            retrieval_top_k=int(os.getenv("VIDSEARCH_RETRIEVAL_TOP_K", "20")),
            qdrant_url=os.getenv("VIDSEARCH_QDRANT_URL", "http://localhost:6333"),
            database_url=os.getenv(
                "VIDSEARCH_DATABASE_URL", "sqlite:///data/vidsearch.db"
            ),
        )
