"""Shared pytest fixtures for the vidsearch test suite."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


class FakeImageEncoder:
    def encode_images(self, images: list[bytes]) -> list[tuple[float, float]]:
        return [
            (1.0, 0.0) if image == b"ganpati frame" else (0.0, 1.0) for image in images
        ]

    def encode_text(self, _text: str) -> tuple[float, float]:
        return (1.0, 0.0)


@pytest.fixture
def visual_test_doubles() -> Callable[[Any], None]:
    def configure(app: Any) -> None:
        encoder = FakeImageEncoder()
        app.state.image_encoder = encoder
        app.state.visual_index.encoder = encoder
        app.state.frame_sampler = lambda path, _rate: [
            (
                0.0,
                b"ganpati frame"
                if path.read_bytes() == b"ganpati"
                else b"generic frame",
            )
        ]

    return configure


@pytest.fixture
def test_id() -> str:
    """Return an identifier suitable for isolating test-created records."""
    return uuid.uuid4().hex


@pytest.fixture
def media_dir(tmp_path: Path) -> Path:
    """Return an empty, test-owned directory for temporary media."""
    directory = tmp_path / "media"
    directory.mkdir()
    return directory
