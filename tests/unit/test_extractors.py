"""Unit-test scaffold for extractor plugin contracts."""

import pytest


@pytest.mark.parametrize("extractor_name", ["visual", "speech", "caption"])
def test_enabled_extractor_returns_valid_evidence(extractor_name: str) -> None:
    pytest.skip("Implement when the shared Segment and Evidence APIs are available.")
