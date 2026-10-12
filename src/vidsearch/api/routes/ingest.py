"""Video upload endpoint."""

from __future__ import annotations

from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from vidsearch.api.indexing import index_video
from vidsearch.ingestion.downloader import (
    DownloaderUnavailable,
    VideoDownloadError,
    download_video,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])


class VideoURLRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_video(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
) -> dict[str, object]:
    library = request.app.state.video_library
    try:
        target = library.begin_upload(file.filename)
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error

    size_bytes = 0
    try:
        with target.temporary_path.open("xb") as output:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > library.max_video_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"upload exceeds the {library.max_video_bytes}-byte limit",
                    )
                output.write(chunk)
        if size_bytes == 0:
            raise HTTPException(status_code=422, detail="uploaded video is empty")
        try:
            library.finalize_upload(target, size_bytes)
        except ValueError as error:
            raise HTTPException(status_code=413, detail=str(error)) from error
        library.update_status(target.video_id, "indexing")
        background_tasks.add_task(
            index_video,
            target.video_id,
            library,
            request.app.state.search_index,
            request.app.state.transcriber,
            request.app.state.visual_index,
            request.app.state.image_encoder,
            request.app.state.frame_sampler,
            request.app.state.settings.frame_rate,
        )
        record = library.get_video(target.video_id)
        if record is None:
            raise RuntimeError("uploaded video record disappeared before response")
        return record
    finally:
        target.temporary_path.unlink(missing_ok=True)
        await file.close()


@router.post("/url", status_code=status.HTTP_201_CREATED)
def import_video_url(
    body: VideoURLRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> dict[str, object]:
    library = request.app.state.video_library
    try:
        with TemporaryDirectory(dir=library.data_dir) as download_dir:
            downloaded = download_video(
                body.url,
                download_dir,
                library.max_video_bytes,
                library.max_video_duration_seconds,
            )
            target = library.begin_upload(downloaded.filename)
            size_bytes = downloaded.path.stat().st_size
            if size_bytes < 1:
                raise HTTPException(status_code=422, detail="downloaded video is empty")
            if size_bytes > library.max_video_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"video exceeds the {library.max_video_bytes}-byte limit",
                )
            try:
                with downloaded.path.open("rb") as source:
                    with target.temporary_path.open("xb") as output:
                        while chunk := source.read(1024 * 1024):
                            output.write(chunk)
                try:
                    library.finalize_upload(target, size_bytes)
                except ValueError as error:
                    raise HTTPException(status_code=413, detail=str(error)) from error
            finally:
                target.temporary_path.unlink(missing_ok=True)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except DownloaderUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except VideoDownloadError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    library.update_status(target.video_id, "indexing")
    background_tasks.add_task(
        index_video,
        target.video_id,
        library,
        request.app.state.search_index,
        request.app.state.transcriber,
        request.app.state.visual_index,
        request.app.state.image_encoder,
        request.app.state.frame_sampler,
        request.app.state.settings.frame_rate,
    )
    updated_record = library.get_video(target.video_id)
    if updated_record is None:
        raise RuntimeError("imported video record disappeared before response")
    return updated_record
