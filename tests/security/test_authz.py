"""Security-test scaffold for cross-user authorization boundaries."""

import pytest


def test_user_cannot_read_or_delete_another_users_video() -> None:
    pytest.skip(
        "Implement when authentication and video ownership contracts are available."
    )
