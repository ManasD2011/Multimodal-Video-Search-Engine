"""Background job status endpoints."""

from fastapi import APIRouter, FastAPI

router = APIRouter()


def register_routes(app: FastAPI) -> None:
    app.include_router(router, prefix="/jobs", tags=["jobs"])
