"""Metadata persistence interface; SQLAlchemy models can implement this contract."""

from typing import Protocol

from vidsearch.core.schemas import Evidence, Segment


class MetadataStore(Protocol):
    def save_segment(self, segment: Segment) -> None: ...

    def save_evidence(self, evidence: Evidence) -> None: ...

    def delete_video(self, video_id: str) -> None: ...
