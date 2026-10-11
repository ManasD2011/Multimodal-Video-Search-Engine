"""Search orchestration across configured retrieval backends."""

from collections.abc import Callable, Sequence

from vidsearch.core.schemas import Query, SearchHit, SearchResult
from vidsearch.retrieval.fusion import reciprocal_rank_fusion


class SearchEngine:
    def __init__(
        self,
        retrievers: Sequence[Callable[[Query], list[SearchHit]]],
    ) -> None:
        self.retrievers = tuple(retrievers)

    def search(self, query: Query) -> SearchResult:
        if not self.retrievers:
            raise RuntimeError("no retrieval backends are configured")
        result_lists = [retriever(query) for retriever in self.retrievers]
        fused = reciprocal_rank_fusion(result_lists)[: query.top_k]
        return SearchResult(
            query=query,
            hits=tuple(fused),
            total=len(fused),
            sources=tuple(f"retriever_{index}" for index in range(len(result_lists))),
        )
