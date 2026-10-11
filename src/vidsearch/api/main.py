"""FastAPI application factory entry point."""

from __future__ import annotations

import os

from vidsearch.core.config import Settings


def create_app(settings: Settings | None = None):
    """Create the API after FastAPI is included in the application dependencies."""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:
        raise RuntimeError("install FastAPI to run the HTTP API") from exc

    app = FastAPI(title="Video Search API")
    app_settings = settings or Settings.from_env()
    from vidsearch.api.library import VideoLibrary
    from vidsearch.api.routes.ingest import router as ingest_router
    from vidsearch.api.routes.jobs import router as jobs_router
    from vidsearch.api.routes.search import router as search_router
    from vidsearch.api.routes.videos import router as videos_router

    app.state.settings = app_settings
    app.state.video_library = VideoLibrary(
        app_settings.data_dir, app_settings.max_video_bytes
    )
    app.state.search_engine = None

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
