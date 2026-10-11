"""Unit-test scaffold for temporal hit grouping and selection policies."""

import pytest


@pytest.mark.parametrize("policy", ["earliest", "all", "best"])
def test_temporal_policy_returns_expected_candidate_groups(policy: str) -> None:
    pytest.skip("Implement when the temporal retrieval API is available.")
