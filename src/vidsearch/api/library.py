"""Local SQLite-backed video library for the development API."""

from __future__ import annotations

import json
import mimetypes
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from threading import Lock
from typing import Literal, TypedDict

from vidsearch.core.security import ALLOWED_VIDEO_SUFFIXES

VideoStatus = Literal["uploaded", "indexing", "ready", "failed"]


class TranscriptSegment(TypedDict):
    segment_id: str
    video_id: str
    start_seconds: float
    end_seconds: float
    text: str


class VisualSegment(TypedDict):
    segment_id: str
    video_id: str
    start_seconds: float
    end_seconds: float
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class UploadTarget:
    video_id: str
    filename: str
    temporary_path: Path
    media_path: Path


class VideoLibrary:
    """Persist uploaded files and library metadata in the configured data root."""

    def __init__(
        self, data_dir: Path, max_video_bytes: int, max_video_duration_seconds: int
    ) -> None:
        if max_video_bytes < 1 or max_video_duration_seconds < 1:
            raise ValueError("video limits must be positive")
        self.data_dir = data_dir.expanduser().resolve()
        self.media_dir = self.data_dir / "videos"
        self.database_path = self.data_dir / "vidsearch.sqlite3"
        self.max_video_bytes = max_video_bytes
        self.max_video_duration_seconds = max_video_duration_seconds
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
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'uploaded',
                    duration_seconds REAL,
                    segment_count INTEGER NOT NULL DEFAULT 0,
                    processing_error TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS visual_segments (
                    segment_id TEXT PRIMARY KEY,
                    video_id TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
                    start_seconds REAL NOT NULL,
                    end_seconds REAL NOT NULL,
                    embedding TEXT NOT NULL
                )
                """
            )
            columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(videos)")
            }
            for name, definition in (
                ("status", "TEXT NOT NULL DEFAULT 'uploaded'"),
                ("duration_seconds", "REAL"),
                ("segment_count", "INTEGER NOT NULL DEFAULT 0"),
                ("processing_error", "TEXT"),
            ):
                if name not in columns:
                    connection.execute(
                        f"ALTER TABLE videos ADD COLUMN {name} {definition}"
                    )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS transcript_segments (
                    segment_id TEXT PRIMARY KEY,
                    video_id TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
                    start_seconds REAL NOT NULL,
                    end_seconds REAL NOT NULL,
                    text TEXT NOT NULL
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
                SELECT video_id, filename, media_filename, size_bytes, created_at,
                       status, duration_seconds, segment_count, processing_error
                FROM videos
                ORDER BY created_at DESC, video_id DESC
                """
            ).fetchall()
        return [self._serialize(dict(row)) for row in rows]

    def get_video(self, video_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT video_id, filename, media_filename, size_bytes, created_at,
                       status, duration_seconds, segment_count, processing_error
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

    def update_status(
        self, video_id: str, status: VideoStatus, processing_error: str | None = None
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE videos
                SET status = ?, processing_error = ?
                WHERE video_id = ?
                """,
                (status, processing_error, video_id),
            )
        return cursor.rowcount > 0

    def save_transcript(
        self,
        video_id: str,
        chunks: list[tuple[float, float, str]],
        duration_seconds: float,
    ) -> None:
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM videos WHERE video_id = ?", (video_id,)
            ).fetchone()
            if exists is None:
                raise LookupError(f"video {video_id} no longer exists")
            connection.execute(
                "DELETE FROM transcript_segments WHERE video_id = ?", (video_id,)
            )
            connection.execute(
                "DELETE FROM visual_segments WHERE video_id = ?", (video_id,)
            )
            connection.executemany(
                """
                INSERT INTO transcript_segments
                    (segment_id, video_id, start_seconds, end_seconds, text)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (f"{video_id}:{index}", video_id, start, end, text)
                    for index, (start, end, text) in enumerate(chunks)
                ],
            )
            connection.execute(
                """
                UPDATE videos
                SET status = 'indexing', duration_seconds = ?, segment_count = ?,
                    processing_error = NULL
                WHERE video_id = ?
                """,
                (duration_seconds, len(chunks), video_id),
            )

    def transcript_segments(
        self, video_id: str | None = None
    ) -> list[TranscriptSegment]:
        with self._connect() as connection:
            rows = connection.execute(
                (
                    """
                    SELECT segment_id, video_id, start_seconds, end_seconds, text
                    FROM transcript_segments
                    WHERE video_id = ?
                    ORDER BY start_seconds, segment_id
                    """
                    if video_id is not None
                    else """
                    SELECT segment_id, video_id, start_seconds, end_seconds, text
                    FROM transcript_segments
                    ORDER BY video_id, start_seconds, segment_id
                    """
                ),
                (video_id,) if video_id is not None else (),
            ).fetchall()
        return [
            {
                "segment_id": str(row["segment_id"]),
                "video_id": str(row["video_id"]),
                "start_seconds": float(row["start_seconds"]),
                "end_seconds": float(row["end_seconds"]),
                "text": str(row["text"]),
            }
            for row in rows
        ]

    def save_visual_segments(
        self,
        video_id: str,
        frames: list[tuple[float, float, tuple[float, ...]]],
    ) -> None:
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM videos WHERE video_id = ?", (video_id,)
            ).fetchone()
            if exists is None:
                raise LookupError(f"video {video_id} no longer exists")
            connection.execute(
                "DELETE FROM visual_segments WHERE video_id = ?", (video_id,)
            )
            connection.executemany(
                """
                INSERT INTO visual_segments
                    (segment_id, video_id, start_seconds, end_seconds, embedding)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        f"{video_id}:visual:{index}",
                        video_id,
                        start,
                        end,
                        json.dumps(embedding),
                    )
                    for index, (start, end, embedding) in enumerate(frames)
                ],
            )
            connection.execute(
                """
                UPDATE videos
                SET segment_count = (
                    SELECT COUNT(*) FROM transcript_segments WHERE video_id = ?
                ) + ?, processing_error = NULL
                WHERE video_id = ?
                """,
                (video_id, len(frames), video_id),
            )

    def visual_segments(self) -> list[VisualSegment]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT segment_id, video_id, start_seconds, end_seconds, embedding
                FROM visual_segments
                ORDER BY video_id, start_seconds, segment_id
                """
            ).fetchall()
        segments: list[VisualSegment] = []
        for row in rows:
            embedding = json.loads(str(row["embedding"]))
            if not isinstance(embedding, list) or not all(
                isinstance(value, (int, float)) for value in embedding
            ):
                raise ValueError("stored visual embedding must be a numeric list")
            segments.append(
                {
                    "segment_id": str(row["segment_id"]),
                    "video_id": str(row["video_id"]),
                    "start_seconds": float(row["start_seconds"]),
                    "end_seconds": float(row["end_seconds"]),
                    "embedding": [float(value) for value in embedding],
                }
            )
        return segments

    def delete_video(self, video_id: str) -> bool:
        with self._lock:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT media_filename FROM videos WHERE video_id = ?",
                    (video_id,),
                ).fetchone()
                if row is None:
                    return False
                connection.execute(
                    "DELETE FROM transcript_segments WHERE video_id = ?",
                    (video_id,),
                )
                connection.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
            path = (self.media_dir / row["media_filename"]).resolve()
            if path.is_relative_to(self.media_dir):
                path.unlink(missing_ok=True)
        return True

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
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
            "duration_seconds": row.get("duration_seconds"),
            "segment_count": row.get("segment_count", 0),
            "status": row.get("status", "uploaded"),
            "processing_error": row.get("processing_error"),
            "added_at": row["created_at"],
            "size_bytes": row["size_bytes"],
            "media_type": media_type,
            "media_url": f"/videos/{row['video_id']}/media",
        }
