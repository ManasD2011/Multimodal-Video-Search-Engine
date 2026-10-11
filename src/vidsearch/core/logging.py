"""Logging helpers for consistent application logger naming."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a logger namespaced under ``vidsearch``."""
    if not name.strip():
        raise ValueError("logger name must not be empty")
    return logging.getLogger(
        name if name.startswith("vidsearch") else f"vidsearch.{name}"
    )
