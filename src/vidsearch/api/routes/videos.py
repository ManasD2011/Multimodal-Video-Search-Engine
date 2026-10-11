"""Video library endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("")
def list_videos(request: Request) -> list[dict[str, object]]:
    return request.app.state.video_library.list_videos()


@router.get("/{video_id}")
def get_video(video_id: str, request: Request) -> dict[str, object]:
    video = request.app.state.video_library.get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="video not found")
    return video


@router.get("/{video_id}/media")
def get_video_media(video_id: str, request: Request) -> FileResponse:
    media = request.app.state.video_library.media_path(video_id)
    if media is None:
        raise HTTPException(status_code=404, detail="video media not found")
    path, media_type = media
    return FileResponse(path, media_type=media_type)


@router.delete("/{video_id}", status_code=204)
def delete_video(video_id: str, request: Request) -> None:
    if not request.app.state.video_library.delete_video(video_id):
        raise HTTPException(status_code=404, detail="video not found")
