"""Shared pytest fixtures for the vidsearch test suite."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest


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
