from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vidsearch.api.main import create_app
from vidsearch.core.config import Settings
from vidsearch.ingestion.downloader import DownloadedVideo
from vidsearch.ingestion.transcription import TranscriptChunk, Transcription


@pytest.fixture
def client(tmp_path: Path, visual_test_doubles) -> TestClient:
    app = create_app(
        Settings(
            data_dir=tmp_path,
            max_video_bytes=8,
            max_video_duration_seconds=60,
        )
    )
    app.state.transcriber = lambda _path, _cache: Transcription(
        duration_seconds=10,
        chunks=(TranscriptChunk(1.0, 4.0, "A red umbrella opens."),),
    )
    visual_test_doubles(app)
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_search_readiness_are_explicit(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "search_ready": True}

    search = client.post("/search", json={"query": "a red umbrella"})
    assert search.status_code == 200
    assert search.json()["hits"] == []


def test_upload_list_media_and_delete_video(client: TestClient) -> None:
    uploaded = client.post(
        "/ingest/upload",
        files={"file": ("travel clip.mp4", b"sample-video-data", "video/mp4")},
    )
    assert uploaded.status_code == 413

    uploaded = client.post(
        "/ingest/upload",
        files={"file": ("travel clip.mp4", b"video", "video/mp4")},
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["status"] == "indexing"
    record = client.get("/videos").json()[0]
    assert record["filename"] == "travel clip.mp4"
    assert record["status"] == "ready"
    assert record["duration_seconds"] == 10
    assert record["segment_count"] == 2
    assert client.get("/videos").json() == [record]

    search = client.post("/search", json={"query": "red umbrella"})
    assert search.status_code == 200
    assert search.json()["hits"][0]["video_id"] == record["video_id"]
    assert search.json()["hits"][0]["start_seconds"] == 1
    assert search.json()["hits"][0]["evidence"] == [
        {"stream": "speech", "text": "A red umbrella opens."}
    ]

    media = client.get(record["media_url"])
    assert media.status_code == 200
    assert media.content == b"video"
    assert media.headers["content-type"].startswith("video/mp4")

    deleted = client.delete(f"/videos/{record['video_id']}")
    assert deleted.status_code == 204
    assert client.get(f"/videos/{record['video_id']}").status_code == 404
    assert client.get(record["media_url"]).status_code == 404
    assert client.post("/search", json={"query": "red umbrella"}).json()["hits"] == []


@pytest.mark.parametrize(
    ("filename", "expected_status"),
    [
        ("document.txt", 415),
        ("../outside.mp4", 201),
        ("", 422),
    ],
)
def test_upload_filename_is_safely_normalized(
    client: TestClient, filename: str, expected_status: int
) -> None:
    response = client.post(
        "/ingest/upload",
        files={"file": (filename, b"clip", "application/octet-stream")},
    )
    assert response.status_code == expected_status
    if response.status_code == 201:
        assert response.json()["filename"] == "outside.mp4"


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/ingest/upload",
        files={"file": ("empty.mp4", b"", "video/mp4")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "uploaded video is empty"


def test_upload_rejects_query_outside_contract(client: TestClient) -> None:
    assert client.post("/search", json={"query": ""}).status_code == 422
    assert (
        client.post("/search", json={"query": "valid", "top_k": 101}).status_code == 422
    )


def test_youtube_url_import_downloads_and_indexes_video(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from vidsearch.api.routes import ingest

    def fake_download(
        url: str, destination: str | Path, _max_bytes: int, _max_duration: int
    ) -> DownloadedVideo:
        assert url == "https://youtu.be/example"
        media_path = Path(destination) / "download.mp4"
        media_path.write_bytes(b"video")
        return DownloadedVideo(media_path, "A trip.mp4", 10)

    monkeypatch.setattr(ingest, "download_video", fake_download)
    response = client.post("/ingest/url", json={"url": "https://youtu.be/example"})
    assert response.status_code == 201
    assert response.json()["status"] == "indexing"
    record = client.get("/videos").json()[0]
    assert record["filename"] == "A trip.mp4"
    assert record["status"] == "ready"
    assert (
        client.post("/search", json={"query": "red umbrella"}).json()["hits"][0][
            "video_id"
        ]
        == record["video_id"]
    )


def test_invalid_youtube_url_is_rejected(client: TestClient) -> None:
    response = client.post("/ingest/url", json={"url": "http://127.0.0.1/video.mp4"})
    assert response.status_code == 422


def test_transcription_failure_is_visible_in_library(client: TestClient) -> None:
    def fail_transcription(_path: Path, _cache: Path) -> Transcription:
        raise RuntimeError("speech model is unavailable")

    client.app.state.transcriber = fail_transcription
    response = client.post(
        "/ingest/upload",
        files={"file": ("failed.mp4", b"video", "video/mp4")},
    )
    assert response.status_code == 201
    record = client.get(f"/videos/{response.json()['video_id']}").json()
    assert record["status"] == "failed"
    assert record["processing_error"] == "speech model is unavailable"


def test_visual_description_finds_a_timestamped_frame_after_restart(
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
        chunks=(),
    )
    visual_test_doubles(app)

    with TestClient(app) as client:
        upload = client.post(
            "/ingest/upload",
            files={"file": ("ganpati.mp4", b"ganpati", "video/mp4")},
        )
        assert upload.status_code == 201
        video_id = upload.json()["video_id"]
        assert client.get(f"/videos/{video_id}").json()["status"] == "ready"

        result = client.post("/search", json={"query": "Ganpati idol"})
        assert result.status_code == 200
        assert result.json()["total"] == 1
        hit = result.json()["hits"][0]
        assert hit["video_id"] == video_id
        assert hit["start_seconds"] == 0
        assert hit["end_seconds"] == 1
        assert hit["evidence"] == [{"stream": "visual", "text": None}]

    restarted_app = create_app(settings)
    visual_test_doubles(restarted_app)
    with TestClient(restarted_app) as client:
        result = client.post("/search", json={"query": "Ganpati idol"})
        assert result.status_code == 200
        assert result.json()["hits"][0]["video_id"] == video_id
