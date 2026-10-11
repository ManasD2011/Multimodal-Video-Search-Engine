"""Validated representation of a search plan."""

from dataclasses import dataclass

ALLOWED_MODALITIES = frozenset({"visual", "speech", "caption", "ocr", "audio_events"})


@dataclass(frozen=True, slots=True)
class QueryPlan:
    modalities: tuple[str, ...]
    intent: str = "semantic"
    attributes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        unknown = set(self.modalities) - ALLOWED_MODALITIES
        if unknown:
            raise ValueError(f"unsupported modalities: {', '.join(sorted(unknown))}")
        if not self.modalities:
            raise ValueError("query plan must include at least one modality")
        if not self.intent.strip():
            raise ValueError("query plan intent must not be empty")
