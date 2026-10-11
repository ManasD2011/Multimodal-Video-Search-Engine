"""Integration-test scaffold for background ingestion job lifecycle."""

import pytest


def test_ingest_job_transitions_to_terminal_status() -> None:
    pytest.skip("Requires the worker queue and job persistence APIs.")
