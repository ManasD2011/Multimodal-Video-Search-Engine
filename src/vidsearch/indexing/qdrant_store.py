"""Vector-store adapter contract for Qdrant."""

from collections.abc import Sequence
from typing import Protocol

from vidsearch.core.schemas import Evidence, Query, SearchHit


class VectorStore(Protocol):
    def upsert(self, evidence: Sequence[Evidence]) -> None: ...

    def search(self, query: Query, vector: Sequence[float]) -> list[SearchHit]: ...

    def delete_video(self, video_id: str) -> None: ...


class QdrantStore:
    """Qdrant implementation is supplied when the storage dependency is configured."""

    def upsert(self, evidence: Sequence[Evidence]) -> None:
        raise NotImplementedError("configure the Qdrant client and collection schema")

    def search(self, query: Query, vector: Sequence[float]) -> list[SearchHit]:
        raise NotImplementedError("configure the Qdrant client and collection schema")

    def delete_video(self, video_id: str) -> None:
        raise NotImplementedError("configure the Qdrant client and collection schema")
