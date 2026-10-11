"""Object detection and tracking extractor adapter."""

from vidsearch.core.schemas import Evidence, Segment
from vidsearch.extractors.base import Extractor


class DetectionExtractor(Extractor):
    name = "detection"

    def run(self, segment: Segment) -> Evidence:
        raise NotImplementedError("configure an open-vocabulary detector and tracker")
