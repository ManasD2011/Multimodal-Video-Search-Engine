"""Unit-test scaffold for scene and fixed-window segmentation."""

import pytest


@pytest.mark.parametrize("segmentation_mode", ["scene", "fixed_window"])
def test_segments_are_ordered_non_overlapping_and_within_video(
    segmentation_mode: str,
) -> None:
    pytest.skip(
        "Implement when the segmenter API and video fixture contract are defined."
    )
