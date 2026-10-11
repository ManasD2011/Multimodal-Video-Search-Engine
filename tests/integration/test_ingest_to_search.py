"""Integration-test scaffold for the ingest-to-search flow."""

import pytest


def test_ingested_video_can_be_searched_and_returns_timestamped_evidence() -> None:
    pytest.skip("Requires the ingestion/search APIs and isolated test services.")
