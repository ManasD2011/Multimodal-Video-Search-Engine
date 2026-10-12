"""Security checks for URL-based video imports."""

import socket

import pytest

from vidsearch.ingestion.downloader import validate_download_url


@pytest.mark.parametrize(
    "url",
    [
        "http://youtube.com/watch?v=abc",
        "https://127.0.0.1/video.mp4",
        "https://localhost/video.mp4",
        "https://user" + ":password@" + "youtube.com/watch?v=abc",
        "https://youtube.com:8443/watch?v=abc",
        "https://example.com/video.mp4",
    ],
)
def test_downloader_rejects_non_youtube_or_unsafe_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_download_url(url)


def test_downloader_accepts_public_https_youtube_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("142.250.72.14", 443))
        ],
    )
    url = "https://www.youtube.com/watch?v=example"
    assert validate_download_url(url) == url
