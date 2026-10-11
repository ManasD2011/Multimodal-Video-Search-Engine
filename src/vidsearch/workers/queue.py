"""Queue backend interface."""

from collections.abc import Callable
from typing import Protocol


class Queue(Protocol):
    def enqueue(self, function: Callable[..., object], *args: object) -> str: ...


def get_queue() -> Queue:
    """Return the configured RQ/Celery queue adapter."""
    raise NotImplementedError("configure a Redis-backed worker queue")
