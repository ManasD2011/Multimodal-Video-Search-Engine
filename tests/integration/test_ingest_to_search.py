"""End-to-end coverage for local speech indexing and search."""

from pathlib import Path

from fastapi.testclient import TestClient

from vidsearch.api.main import create_app
from vidsearch.core.config import Settings
from vidsearch.ingestion.transcription import TranscriptChunk, Transcription


def test_uploaded_video_transcript_is_searchable_after_restart(
    tmp_path: Path, visual_test_doubles
) -> None:
    settings = Settings(
        data_dir=tmp_path,
        max_video_bytes=32,
        max_video_duration_seconds=60,
    )
    app = create_app(settings)
    app.state.transcriber = lambda _path, _cache: Transcription(
        duration_seconds=10,
        chunks=(TranscriptChunk(2.0, 5.0, "The train arrives at the station."),),
    )
    visual_test_doubles(app)

    with TestClient(app) as client:
        upload = client.post(
            "/ingest/upload",
            files={"file": ("train.mp4", b"video", "video/mp4")},
        )
        assert upload.status_code == 201
        assert upload.json()["status"] == "indexing"
        video_id = upload.json()["video_id"]

        indexed = client.get(f"/videos/{video_id}").json()
        assert indexed["status"] == "ready"
        assert indexed["segment_count"] == 2

    restarted_app = create_app(settings)
    visual_test_doubles(restarted_app)
    with TestClient(restarted_app) as client:
        result = client.post("/search", json={"query": "train station"})
        assert result.status_code == 200
        assert result.json()["total"] == 1
        hit = result.json()["hits"][0]
        assert hit["video_id"] == video_id
        assert hit["start_seconds"] == 2
        assert hit["end_seconds"] == 5
        assert hit["score"] > 0
        assert hit["evidence"] == [
            {"stream": "speech", "text": "The train arrives at the station."}
        ]
