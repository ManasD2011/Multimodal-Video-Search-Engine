"""Small in-memory BM25 baseline for text evidence."""

from __future__ import annotations

import math
import re
from collections import Counter
from threading import RLock

from vidsearch.core.schemas import Evidence, Query, SearchHit

TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


class BM25Store:
    """In-memory BM25 index; replace with a persistent backend as data grows."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 parameters must satisfy k1 > 0 and 0 <= b <= 1")
        self.k1 = k1
        self.b = b
        self._documents: dict[str, tuple[Evidence, Counter[str]]] = {}
        self._lock = RLock()

    def add(self, evidence: Evidence) -> None:
        if not evidence.text:
            return
        key = evidence.segment.segment_id or (
            f"{evidence.segment.video_id}:{evidence.segment.start_seconds}"
        )
        tokens = Counter(TOKEN_PATTERN.findall(evidence.text.casefold()))
        with self._lock:
            self._documents[key] = (evidence, tokens)

    def search(self, query: Query) -> list[SearchHit]:
        query_terms = TOKEN_PATTERN.findall(query.text.casefold())
        with self._lock:
            if not query_terms or not self._documents:
                return []
            document_count = len(self._documents)
            average_length: float = sum(
                sum(tokens.values()) for _, tokens in self._documents.values()
            )
            average_length = average_length / document_count
            hits: list[SearchHit] = []
            for evidence, frequencies in self._documents.values():
                length = sum(frequencies.values())
                score = 0.0
                for term in query_terms:
                    term_frequency = frequencies[term]
                    if not term_frequency:
                        continue
                    document_frequency = sum(
                        term in doc for _, doc in self._documents.values()
                    )
                    inverse_frequency = math.log(
                        1
                        + (document_count - document_frequency + 0.5)
                        / (document_frequency + 0.5)
                    )
                    denominator = term_frequency + self.k1 * (
                        1 - self.b + self.b * length / max(average_length, 1e-12)
                    )
                    score += (
                        inverse_frequency * term_frequency * (self.k1 + 1) / denominator
                    )
                if score > 0:
                    hits.append(
                        SearchHit(
                            segment=evidence.segment, score=score, evidence=(evidence,)
                        )
                    )
            return sorted(hits, key=lambda hit: hit.score, reverse=True)[: query.top_k]

    def delete_video(self, video_id: str) -> None:
        with self._lock:
            self._documents = {
                key: item
                for key, item in self._documents.items()
                if item[0].segment.video_id != video_id
            }
