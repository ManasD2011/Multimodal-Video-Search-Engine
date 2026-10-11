"""Visual captioning extractor adapter."""

from vidsearch.core.schemas import Evidence, Segment
from vidsearch.extractors.base import Extractor


class CaptionExtractor(Extractor):
    name = "caption"

    def run(self, segment: Segment) -> Evidence:
        raise NotImplementedError("configure a video/image captioning model adapter")
