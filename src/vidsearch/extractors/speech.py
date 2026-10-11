"""Speech transcription extractor adapter."""

from vidsearch.core.schemas import Evidence, Segment
from vidsearch.extractors.base import Extractor


class SpeechExtractor(Extractor):
    name = "speech"

    def run(self, segment: Segment) -> Evidence:
        raise NotImplementedError("configure a speech-to-text model adapter")
