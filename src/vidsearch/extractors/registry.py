"""Explicit registry for configured extractor plugins."""

from vidsearch.extractors.base import Extractor


class ExtractorRegistry:
    def __init__(self) -> None:
        self._extractors: dict[str, Extractor] = {}

    def register(self, extractor: Extractor) -> None:
        if not extractor.name.strip():
            raise ValueError("extractor name must not be empty")
        if extractor.name in self._extractors:
            raise ValueError(f"extractor already registered: {extractor.name}")
        self._extractors[extractor.name] = extractor

    def get(self, name: str) -> Extractor:
        try:
            return self._extractors[name]
        except KeyError as exc:
            raise KeyError(f"extractor is not registered: {name}") from exc

    def enabled(self, names: tuple[str, ...]) -> tuple[Extractor, ...]:
        return tuple(self.get(name) for name in names)
