"""Base contract for evidence extractor plugins."""

from abc import ABC, abstractmethod

from vidsearch.core.schemas import Evidence, Segment


class Extractor(ABC):
    """An extractor produces one evidence stream for a segment."""

    name: str

    @abstractmethod
    def run(self, segment: Segment) -> Evidence:
        """Extract evidence from a segment."""
