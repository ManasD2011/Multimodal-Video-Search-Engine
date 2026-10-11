from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vidsearch.api.main import create_app
from vidsearch.core.config import Settings


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = create_app(Settings(data_dir=tmp_path, max_video_bytes=8))
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_search_readiness_are_explicit(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "search_ready": False}

    search = client.post("/search", json={"query": "a red umbrella"})
    assert search.status_code == 503
    assert "no retrieval index is configured" in search.json()["detail"]


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
    record = uploaded.json()
    assert record["filename"] == "travel clip.mp4"
    assert record["status"] == "uploaded"
    assert record["duration_seconds"] is None
    assert record["segment_count"] == 0
    assert client.get("/videos").json() == [record]

    media = client.get(record["media_url"])
    assert media.status_code == 200
    assert media.content == b"video"
    assert media.headers["content-type"].startswith("video/mp4")

    deleted = client.delete(f"/videos/{record['video_id']}")
    assert deleted.status_code == 204
    assert client.get(f"/videos/{record['video_id']}").status_code == 404
    assert client.get(record["media_url"]).status_code == 404


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
