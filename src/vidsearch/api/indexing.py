"""Background indexing for locally stored video transcripts."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Protocol

from vidsearch.api.library import VideoLibrary
from vidsearch.core.schemas import Evidence, Segment
from vidsearch.indexing.bm25_store import BM25Store
from vidsearch.indexing.visual_store import VisualIndex, validate_visual_vectors
from vidsearch.ingestion.clip_encoder import Embedding, normalize_embedding
from vidsearch.ingestion.frames import sample_frames
from vidsearch.ingestion.transcription import Transcription, transcribe_video

logger = logging.getLogger(__name__)
Transcriber = Callable[[Path, Path], Transcription]
FrameSampler = Callable[[Path, float], Iterable[tuple[float, bytes]]]


class ImageEncoder(Protocol):
    def encode_images(self, images: Sequence[bytes]) -> list[Embedding]: ...


def load_saved_transcripts(library: VideoLibrary, index: BM25Store) -> None:
    for row in library.transcript_segments():
        segment = Segment(
            video_id=str(row["video_id"]),
            start_seconds=float(row["start_seconds"]),
            end_seconds=float(row["end_seconds"]),
            segment_id=str(row["segment_id"]),
        )
        index.add(Evidence(segment=segment, stream="speech", text=str(row["text"])))


def load_saved_visuals(library: VideoLibrary, index: VisualIndex) -> None:
    for row in library.visual_segments():
        segment = Segment(
            video_id=str(row["video_id"]),
            start_seconds=float(row["start_seconds"]),
            end_seconds=float(row["end_seconds"]),
            segment_id=str(row["segment_id"]),
        )
        embedding = tuple(float(value) for value in row["embedding"])
        index.add(Evidence(segment=segment, stream="visual", vector=embedding))


def index_video(
    video_id: str,
    library: VideoLibrary,
    index: BM25Store,
    transcriber: Transcriber = transcribe_video,
    visual_index: VisualIndex | None = None,
    image_encoder: ImageEncoder | None = None,
    frame_sampler: FrameSampler = sample_frames,
    frames_per_second: float = 1.0,
) -> None:
    if not library.update_status(video_id, "indexing"):
        return
    try:
        media = library.media_path(video_id)
        if media is None:
            raise FileNotFoundError("video media is missing")
        media_path, _ = media
        saved_transcript = library.transcript_segments(video_id)
        if saved_transcript:
            record = library.get_video(video_id)
            if record is None:
                raise LookupError(f"video {video_id} no longer exists")
            duration_seconds = float(record["duration_seconds"] or 0)
            evidence_items = [
                Evidence(
                    segment=Segment(
                        video_id=video_id,
                        start_seconds=float(row["start_seconds"]),
                        end_seconds=float(row["end_seconds"]),
                        segment_id=str(row["segment_id"]),
                    ),
                    stream="speech",
                    text=str(row["text"]),
                )
                for row in saved_transcript
            ]
        else:
            transcription = transcriber(media_path, library.data_dir / "models")
            duration_seconds = transcription.duration_seconds
            evidence_items = []
            chunks: list[tuple[float, float, str]] = []
            for chunk in transcription.chunks:
                text = chunk.text.strip()
                if not text:
                    continue
                segment = Segment(
                    video_id=video_id,
                    start_seconds=chunk.start_seconds,
                    end_seconds=chunk.end_seconds,
                    segment_id=f"{video_id}:{len(chunks)}",
                )
                chunks.append((segment.start_seconds, segment.end_seconds, text))
                evidence_items.append(
                    Evidence(segment=segment, stream="speech", text=text)
                )
            library.save_transcript(video_id, chunks, duration_seconds)

        if duration_seconds > library.max_video_duration_seconds:
            raise ValueError(
                "video exceeds the "
                f"{library.max_video_duration_seconds}-second duration limit"
            )

        index.delete_video(video_id)
        for evidence in evidence_items:
            index.add(evidence)

        if visual_index is not None:
            if image_encoder is None:
                raise RuntimeError(
                    "visual indexing was enabled without an image encoder"
                )
            interval = 1.0 / frames_per_second
            visual_frames: list[tuple[float, float, Embedding]] = []
            pending: list[tuple[float, bytes]] = []
            for frame in frame_sampler(media_path, frames_per_second):
                pending.append(frame)
                if len(pending) == 8:
                    visual_frames.extend(
                        _encode_frame_batch(
                            pending, image_encoder, duration_seconds, interval
                        )
                    )
                    pending.clear()
            if pending:
                visual_frames.extend(
                    _encode_frame_batch(
                        pending, image_encoder, duration_seconds, interval
                    )
                )
            if not visual_frames:
                raise ValueError("no video frames could be extracted for visual search")

            library.save_visual_segments(video_id, visual_frames)
            visual_index.delete_video(video_id)
            for frame_index, (start, end, embedding) in enumerate(visual_frames):
                segment = Segment(
                    video_id=video_id,
                    start_seconds=start,
                    end_seconds=end,
                    segment_id=f"{video_id}:visual:{frame_index}",
                )
                visual_index.add(
                    Evidence(segment=segment, stream="visual", vector=embedding)
                )
        library.update_status(video_id, "ready")
    except Exception as error:
        logger.exception("Failed to index video %s", video_id)
        if isinstance(error, (FileNotFoundError, RuntimeError, ValueError)):
            message = str(error)
        else:
            message = f"Indexing failed ({type(error).__name__}); see backend logs."
        library.update_status(video_id, "failed", message[:500])


def _encode_frame_batch(
    frames: list[tuple[float, bytes]],
    encoder: ImageEncoder,
    duration_seconds: float,
    interval: float,
) -> list[tuple[float, float, Embedding]]:
    vectors = encoder.encode_images([image for _, image in frames])
    validate_visual_vectors(vectors, len(frames))
    encoded: list[tuple[float, float, Embedding]] = []
    for (start, _), vector in zip(frames, vectors, strict=True):
        if start < 0 or start >= duration_seconds:
            raise ValueError("frame timestamp is outside the video duration")
        end = min(duration_seconds, start + interval)
        encoded.append((start, end, normalize_embedding(vector)))
    return encoded
