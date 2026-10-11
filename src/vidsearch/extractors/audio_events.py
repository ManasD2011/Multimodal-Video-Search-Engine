"""Audio event classification extractor adapter."""

from vidsearch.core.schemas import Evidence, Segment
from vidsearch.extractors.base import Extractor


class AudioEventExtractor(Extractor):
    name = "audio_events"

    def run(self, segment: Segment) -> Evidence:
        raise NotImplementedError("configure a CLAP-compatible audio model adapter")
