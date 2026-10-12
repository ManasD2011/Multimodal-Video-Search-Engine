"""Local CLIP image-text embeddings for visual video search."""

from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO
from pathlib import Path
from threading import RLock

import numpy as np

Embedding = tuple[float, ...]


class ClipEncoder:
    """Load a CPU CLIP model on first use and encode text and JPEG frames."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self._model = None
        self._lock = RLock()

    def encode_text(self, text: str) -> Embedding:
        with self._lock:
            model = self._load_model()
            vector = model.encode(
                [text], convert_to_numpy=True, normalize_embeddings=True
            )[0]
        return tuple(float(value) for value in vector)

    def encode_images(self, images: Sequence[bytes]) -> list[Embedding]:
        try:
            from PIL import Image
        except ImportError as error:
            raise RuntimeError(
                "Visual search requires Pillow. Install it with "
                '`python -m pip install -e ".[visual]`.'
            ) from error

        decoded = [Image.open(BytesIO(image)).convert("RGB") for image in images]
        with self._lock:
            model = self._load_model()
            vectors = model.encode(
                decoded,
                batch_size=8,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        return [tuple(float(value) for value in vector) for vector in vectors]

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as error:
                raise RuntimeError(
                    "Visual search dependencies are missing. Install them with "
                    '`python -m pip install -e ".[visual]`.'
                ) from error
            self._model = SentenceTransformer(
                "clip-ViT-B-32",
                cache_folder=str(self.cache_dir),
                device="cpu",
            )
        return self._model


def normalize_embedding(vector: Sequence[float]) -> Embedding:
    values = np.asarray(vector, dtype=np.float32)
    if values.ndim != 1 or not values.size or not np.isfinite(values).all():
        raise ValueError("visual embeddings must be non-empty finite vectors")
    norm = float(np.linalg.norm(values))
    if norm == 0:
        raise ValueError("visual embeddings must not be zero vectors")
    return tuple(float(value) for value in values / norm)
