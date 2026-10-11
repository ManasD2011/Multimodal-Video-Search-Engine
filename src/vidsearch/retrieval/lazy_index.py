"""Candidate-only enrichment interface for query-time captioning."""

from collections.abc import Sequence

from vidsearch.core.schemas import Evidence, SearchHit


def enrich_candidates(candidates: Sequence[SearchHit]) -> list[Evidence]:
    """Generate richer evidence for a bounded candidate set on demand."""
    raise NotImplementedError("configure query-time visual captioning")
