"""Optical character recognition extractor adapter."""

from vidsearch.core.schemas import Evidence, Segment
from vidsearch.extractors.base import Extractor


class OCRExtractor(Extractor):
    name = "ocr"

    def run(self, segment: Segment) -> Evidence:
        raise NotImplementedError("configure an OCR model adapter")
