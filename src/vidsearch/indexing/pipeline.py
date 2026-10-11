"""Ingestion orchestration contracts."""

from collections.abc import Iterable, Sequence

from vidsearch.core.schemas import Evidence, Segment
from vidsearch.extractors.base import Extractor
from vidsearch.indexing.metadata_db import MetadataStore
from vidsearch.indexing.qdrant_store import VectorStore


class IndexingPipeline:
    def __init__(
        self,
        extractors: Sequence[Extractor],
        vector_store: VectorStore,
        metadata_store: MetadataStore,
    ) -> None:
        self.extractors = tuple(extractors)
        self.vector_store = vector_store
        self.metadata_store = metadata_store

    def index_segments(self, segments: Iterable[Segment]) -> list[Evidence]:
        evidence_items: list[Evidence] = []
        for segment in segments:
            self.metadata_store.save_segment(segment)
            for extractor in self.extractors:
                evidence = extractor.run(segment)
                self.metadata_store.save_evidence(evidence)
                evidence_items.append(evidence)
        self.vector_store.upsert(evidence_items)
        return evidence_items
