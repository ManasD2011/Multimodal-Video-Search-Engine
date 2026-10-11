"""Background task entry points."""

from vidsearch.core.schemas import Segment


def ingest_video(video_id: str, source_path: str) -> list[Segment]:
    """Validate, segment, extract, and index one video."""
    raise NotImplementedError("wire ingestion and indexing services")


def reindex_video(video_id: str) -> None:
    """Rebuild index entries for an existing video."""
    raise NotImplementedError("wire metadata and indexing services")


def delete_video(video_id: str) -> None:
    """Delete a video and its dependent metadata and index entries."""
    raise NotImplementedError("wire persistence adapters and deletion policy")
