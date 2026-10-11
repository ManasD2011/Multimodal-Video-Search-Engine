"""Security-test scaffold for hostile upload inputs."""

import pytest


@pytest.mark.parametrize(
    "attack",
    ["path-traversal", "archive-bomb", "mime-spoofing", "oversized-file"],
)
def test_upload_rejects_malicious_or_out_of_policy_files(attack: str) -> None:
    pytest.skip("Implement when the upload route and configured limits are available.")
