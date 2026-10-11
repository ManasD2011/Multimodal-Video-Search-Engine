"""Local SQLite-backed video library for the development API."""

from __future__ import annotations

import mimetypes
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from threading import Lock

ALLOWED_VIDEO_SUFFIXES = frozenset({".mp4", ".mkv", ".mov", ".webm", ".avi"})


@dataclass(frozen=True, slots=True)
class UploadTarget:
    video_id: str
    filename: str
    temporary_path: Path
    media_path: Path


class VideoLibrary:
    """Persist uploaded files and library metadata in the configured data root."""

    def __init__(self, data_dir: Path, max_video_bytes: int) -> None:
        if max_video_bytes < 1:
            raise ValueError("max_video_bytes must be positive")
        self.data_dir = data_dir.expanduser().resolve()
        self.media_dir = self.data_dir / "videos"
        self.database_path = self.data_dir / "vidsearch.sqlite3"
        self.max_video_bytes = max_video_bytes
        self._lock = Lock()
        self.media_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    video_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    media_filename TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def begin_upload(self, original_filename: str | None) -> UploadTarget:
        if not original_filename:
            raise ValueError("a filename is required")
        filename = PureWindowsPath(original_filename).name
        filename = Path(filename).name.strip()
        if filename in {"", ".", ".."}:
            raise ValueError("a valid filename is required")
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_VIDEO_SUFFIXES:
            raise ValueError(
                f"unsupported video type {suffix or '(no extension)'}; "
                f"allowed types: {', '.join(sorted(ALLOWED_VIDEO_SUFFIXES))}"
            )
        video_id = str(uuid.uuid4())
        media_filename = f"{video_id}{suffix}"
        return UploadTarget(
            video_id=video_id,
            filename=filename,
            temporary_path=self.media_dir / f".{video_id}.upload",
            media_path=self.media_dir / media_filename,
        )

    def finalize_upload(
        self, target: UploadTarget, size_bytes: int
    ) -> dict[str, object]:
        if size_bytes < 1:
            raise ValueError("uploaded video is empty")
        if size_bytes > self.max_video_bytes:
            raise ValueError(f"upload exceeds the {self.max_video_bytes}-byte limit")
        created_at = datetime.now(UTC).isoformat()
        with self._lock:
            target.temporary_path.replace(target.media_path)
            try:
                with self._connect() as connection:
                    connection.execute(
                        """
                        INSERT INTO videos
                            (video_id, filename, media_filename, size_bytes, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            target.video_id,
                            target.filename,
                            target.media_path.name,
                            size_bytes,
                            created_at,
                        ),
                    )
            except sqlite3.Error:
                target.media_path.unlink(missing_ok=True)
                raise
        return self._serialize(
            {
                "video_id": target.video_id,
                "filename": target.filename,
                "media_filename": target.media_path.name,
                "size_bytes": size_bytes,
                "created_at": created_at,
            }
        )

    def list_videos(self) -> list[dict[str, object]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT video_id, filename, media_filename, size_bytes, created_at
                FROM videos
                ORDER BY created_at DESC, video_id DESC
                """
            ).fetchall()
        return [self._serialize(dict(row)) for row in rows]

    def get_video(self, video_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT video_id, filename, media_filename, size_bytes, created_at
                FROM videos WHERE video_id = ?
                """,
                (video_id,),
            ).fetchone()
        return self._serialize(dict(row)) if row else None

    def media_path(self, video_id: str) -> tuple[Path, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT filename, media_filename FROM videos WHERE video_id = ?",
                (video_id,),
            ).fetchone()
        if row is None:
            return None
        path = (self.media_dir / str(row["media_filename"])).resolve()
        if not path.is_relative_to(self.media_dir) or not path.is_file():
            return None
        media_type = mimetypes.guess_type(str(row["filename"]))[0]
        return path, media_type or "application/octet-stream"

    def delete_video(self, video_id: str) -> bool:
        with self._lock:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT media_filename FROM videos WHERE video_id = ?",
                    (video_id,),
                ).fetchone()
                if row is None:
                    return False
                connection.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
            path = (self.media_dir / row["media_filename"]).resolve()
            if path.is_relative_to(self.media_dir):
                path.unlink(missing_ok=True)
        return True

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        with closing(connection):
            with connection:
                yield connection

    @staticmethod
    def _serialize(row: dict[str, object]) -> dict[str, object]:
        filename = str(row["filename"])
        media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return {
            "video_id": row["video_id"],
            "filename": filename,
            "duration_seconds": None,
            "segment_count": 0,
            "status": "uploaded",
            "added_at": row["created_at"],
            "size_bytes": row["size_bytes"],
            "media_type": media_type,
            "media_url": f"/videos/{row['video_id']}/media",
        }
