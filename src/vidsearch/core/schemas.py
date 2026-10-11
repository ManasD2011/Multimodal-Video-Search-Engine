"""Domain models shared by ingestion, indexing, and retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any


@dataclass(frozen=True, slots=True)
class Segment:
    """A time-bounded portion of a source video."""

    video_id: str
    start_seconds: float
    end_seconds: float
    segment_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.video_id.strip():
            raise ValueError("video_id must not be empty")
        if not isfinite(self.start_seconds) or not isfinite(self.end_seconds):
            raise ValueError("segment timestamps must be finite")
        if self.start_seconds < 0 or self.end_seconds <= self.start_seconds:
            raise ValueError(
                "segment must have a positive duration and non-negative start"
            )

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass(frozen=True, slots=True)
class Evidence:
    """Text, vector, or structured evidence extracted from a segment."""

    segment: Segment
    stream: str
    text: str | None = None
    vector: tuple[float, ...] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.stream.strip():
            raise ValueError("evidence stream must not be empty")
        if self.vector is not None and (
            not self.vector or any(not isfinite(value) for value in self.vector)
        ):
            raise ValueError("vector must contain finite values")


@dataclass(frozen=True, slots=True)
class Query:
    """A user search request."""

    text: str
    user_id: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    top_k: int = 10

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("query text must not be empty")
        if self.top_k < 1:
            raise ValueError("top_k must be positive")


@dataclass(frozen=True, slots=True)
class SearchHit:
    """A segment returned by retrieval, with its relevance score."""

    segment: Segment
    score: float
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        if not isfinite(self.score):
            raise ValueError("hit score must be finite")


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Ranked results for a query."""

    query: Query
    hits: tuple[SearchHit, ...]
    total: int
    sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.total < len(self.hits):
            raise ValueError("total cannot be smaller than the returned hit count")
