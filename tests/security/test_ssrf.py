"""Security-test scaffold for server-side request forgery protections."""

import pytest


@pytest.mark.parametrize(
    "target",
    ["loopback", "private-network", "link-local", "redirect-to-private-network"],
)
def test_downloader_blocks_internal_network_targets(target: str) -> None:
    pytest.skip(
        "Implement when URL validation and downloader interfaces are available."
    )
