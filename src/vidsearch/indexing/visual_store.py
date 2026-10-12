"""Thread-safe in-memory similarity search over timestamped visual embeddings."""

from __future__ import annotations

from collections.abc import Sequence
from threading import RLock
from typing import Protocol

import numpy as np

from vidsearch.core.schemas import Evidence, Query, SearchHit
from vidsearch.ingestion.clip_encoder import Embedding, normalize_embedding


class TextEncoder(Protocol):
    def encode_text(self, text: str) -> Embedding: ...


class VisualIndex:
    """Search frame embeddings using the same local CLIP model as text queries."""

    def __init__(self, encoder: TextEncoder, minimum_similarity: float = 0.18) -> None:
        if not -1 <= minimum_similarity <= 1:
            raise ValueError("minimum_similarity must be between -1 and 1")
        self.encoder = encoder
        self.minimum_similarity = minimum_similarity
        self._documents: dict[str, tuple[Evidence, np.ndarray]] = {}
        self._lock = RLock()

    def add(self, evidence: Evidence) -> None:
        if evidence.stream != "visual" or evidence.vector is None:
            raise ValueError(
                "visual index entries require visual evidence and a vector"
            )
        key = evidence.segment.segment_id or (
            f"{evidence.segment.video_id}:{evidence.segment.start_seconds}"
        )
        vector = np.asarray(normalize_embedding(evidence.vector), dtype=np.float32)
        with self._lock:
            self._documents[key] = (evidence, vector)

    def delete_video(self, video_id: str) -> None:
        with self._lock:
            self._documents = {
                key: item
                for key, item in self._documents.items()
                if item[0].segment.video_id != video_id
            }

    def indexed_video_ids(self) -> set[str]:
        with self._lock:
            return {item[0].segment.video_id for item in self._documents.values()}

    def search(self, query: Query) -> list[SearchHit]:
        with self._lock:
            if not self._documents:
                return []
            documents = list(self._documents.values())

        query_vector = np.asarray(
            normalize_embedding(self.encoder.encode_text(query.text)), dtype=np.float32
        )
        if any(vector.shape != query_vector.shape for _, vector in documents):
            raise ValueError("visual query and indexed embeddings have different sizes")
        matrix = np.stack([vector for _, vector in documents])
        similarities = matrix @ query_vector
        ranked_indices = np.argsort(similarities)[::-1]
        hits: list[SearchHit] = []
        for index in ranked_indices:
            score = float(similarities[index])
            if score < self.minimum_similarity:
                break
            evidence = documents[int(index)][0]
            hits.append(
                SearchHit(segment=evidence.segment, score=score, evidence=(evidence,))
            )
            if len(hits) == query.top_k:
                break
        return hits


def validate_visual_vectors(vectors: Sequence[Embedding], expected: int) -> None:
    if len(vectors) != expected:
        raise ValueError(
            f"visual encoder returned {len(vectors)} vectors for {expected} frames"
        )
