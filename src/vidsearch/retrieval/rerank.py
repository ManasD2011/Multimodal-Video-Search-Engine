"""Candidate reranking interface."""

from collections.abc import Sequence

from vidsearch.core.schemas import Query, SearchHit


def rerank(query: Query, candidates: Sequence[SearchHit]) -> list[SearchHit]:
    """Re-score candidates with a configured vision-language model."""
    raise NotImplementedError("configure a vision-language reranker")
