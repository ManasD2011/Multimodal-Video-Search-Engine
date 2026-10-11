"""Visual embedding extractor adapter."""

from vidsearch.core.schemas import Evidence, Segment
from vidsearch.extractors.base import Extractor


class VisualExtractor(Extractor):
    name = "visual"

    def run(self, segment: Segment) -> Evidence:
        raise NotImplementedError("configure a CLIP or SigLIP model adapter")
