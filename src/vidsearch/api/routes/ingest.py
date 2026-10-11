"""Video upload endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_video(
    request: Request, file: Annotated[UploadFile, File()]
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
            return library.finalize_upload(target, size_bytes)
        except ValueError as error:
            raise HTTPException(status_code=413, detail=str(error)) from error
    finally:
        target.temporary_path.unlink(missing_ok=True)
        await file.close()
