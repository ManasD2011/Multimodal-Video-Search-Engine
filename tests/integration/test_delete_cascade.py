"""Integration-test scaffold for video deletion and dependent-index cleanup."""

import pytest


def test_deleting_video_removes_metadata_segments_and_search_vectors() -> None:
    pytest.skip("Requires metadata storage and the configured vector/search indexes.")
