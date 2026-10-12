"""FastAPI application factory entry point."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from vidsearch.core.config import Settings


def create_app(settings: Settings | None = None):
    """Create the API after FastAPI is included in the application dependencies."""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:
        raise RuntimeError("install FastAPI to run the HTTP API") from exc

    app_settings = settings or Settings.from_env()
    from vidsearch.api.indexing import (
        index_video,
        load_saved_transcripts,
        load_saved_visuals,
    )
    from vidsearch.api.library import VideoLibrary
    from vidsearch.api.routes.ingest import router as ingest_router
    from vidsearch.api.routes.jobs import router as jobs_router
    from vidsearch.api.routes.search import router as search_router
    from vidsearch.api.routes.videos import router as videos_router
    from vidsearch.indexing.bm25_store import BM25Store
    from vidsearch.indexing.visual_store import VisualIndex
    from vidsearch.ingestion.clip_encoder import ClipEncoder
    from vidsearch.ingestion.frames import sample_frames
    from vidsearch.ingestion.transcription import transcribe_video
    from vidsearch.retrieval.search import SearchEngine

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        indexed_video_ids = app.state.visual_index.indexed_video_ids()
        for video in app.state.video_library.list_videos():
            missing_visual_index = (
                str(video["video_id"]) not in indexed_video_ids
                and video["duration_seconds"] is not None
            )
            if video["status"] in {"uploaded", "indexing"} or (
                video["status"] in {"ready", "failed"} and missing_visual_index
            ):
                task = asyncio.create_task(
                    asyncio.to_thread(
                        index_video,
                        str(video["video_id"]),
                        app.state.video_library,
                        app.state.search_index,
                        app.state.transcriber,
                        app.state.visual_index,
                        app.state.image_encoder,
                        app.state.frame_sampler,
                        app.state.settings.frame_rate,
                    )
                )
                app.state.index_tasks.add(task)
                task.add_done_callback(app.state.index_tasks.discard)
        try:
            yield
        finally:
            if app.state.index_tasks:
                await asyncio.gather(*app.state.index_tasks)

    app = FastAPI(title="Video Search API", lifespan=lifespan)
    app.state.settings = app_settings
    app.state.video_library = VideoLibrary(
        app_settings.data_dir,
        app_settings.max_video_bytes,
        app_settings.max_video_duration_seconds,
    )
    app.state.search_index = BM25Store()
    load_saved_transcripts(app.state.video_library, app.state.search_index)
    app.state.image_encoder = ClipEncoder(app_settings.data_dir / "models")
    app.state.frame_sampler = sample_frames
    app.state.visual_index = VisualIndex(app.state.image_encoder)
    load_saved_visuals(app.state.video_library, app.state.visual_index)
    app.state.search_engine = SearchEngine(
        [app.state.search_index.search, app.state.visual_index.search]
    )
    app.state.transcriber = transcribe_video
    app.state.index_tasks = set()

    default_origins = "http://localhost:5173,http://127.0.0.1:5173"
    allowed_origins = [
        origin.strip()
        for origin in os.getenv("VIDSEARCH_CORS_ORIGINS", default_origins).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/healthz", tags=["health"])
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "search_ready": app.state.search_engine is not None,
        }

    app.include_router(ingest_router)
    app.include_router(search_router)
    app.include_router(videos_router)
    app.include_router(jobs_router)
    return app
