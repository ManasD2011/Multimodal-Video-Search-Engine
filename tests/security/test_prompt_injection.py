"""Security-test scaffold for untrusted query and video-derived text."""

import pytest


def test_untrusted_text_cannot_override_query_planner_instructions() -> None:
    pytest.skip(
        "Implement when planner prompt boundaries and response schema are defined."
    )
