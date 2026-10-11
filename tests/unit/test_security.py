"""Unit-test scaffold for centralized path, URL, and size validation."""

import pytest


@pytest.mark.parametrize(
    "untrusted_input",
    ["../outside.mp4", "https://127.0.0.1/private", "oversized-upload"],
)
def test_security_validation_rejects_unsafe_inputs(untrusted_input: str) -> None:
    pytest.skip("Implement when the centralized security helper API is available.")
