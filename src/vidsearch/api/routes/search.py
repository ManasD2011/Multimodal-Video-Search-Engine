"""Video search endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from vidsearch.core.schemas import Query

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=20, ge=1, le=100)
    filters: dict[str, Any] = Field(default_factory=dict)


@router.post("")
def search_videos(body: SearchRequest, request: Request) -> dict[str, object]:
    engine = request.app.state.search_engine
    result = engine.search(
        Query(
            text=body.query,
            filters=body.filters,
            top_k=body.top_k,
        )
    )
    return {
        "query": result.query.text,
        "total": result.total,
        "sources": list(result.sources),
        "hits": [
            {
                "video_id": hit.segment.video_id,
                "start_seconds": hit.segment.start_seconds,
                "end_seconds": hit.segment.end_seconds,
                "score": hit.score,
                "evidence": [
                    {"stream": evidence.stream, "text": evidence.text}
                    for evidence in hit.evidence
                ],
            }
            for hit in result.hits
        ],
    }
