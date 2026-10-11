"""Centralized validation for local media paths, remote URLs, and sizes."""

from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlsplit


def validate_local_path(path: str | Path, allowed_root: str | Path) -> Path:
    """Resolve a local path and ensure it remains beneath the configured root."""
    root = Path(allowed_root).expanduser().resolve(strict=True)
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("path is outside the allowed media directory")
    if not resolved.is_file():
        raise ValueError("path must identify a regular file")
    return resolved


def validate_public_url(url: str) -> str:
    """Accept HTTP(S) URLs whose hostname resolves only to public IP addresses."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must use HTTP(S) and include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are not allowed")
    try:
        addresses = {
            ipaddress.ip_address(item[4][0])
            for item in socket.getaddrinfo(
                parsed.hostname, parsed.port, type=socket.SOCK_STREAM
            )
        }
    except (OSError, ValueError) as exc:
        raise ValueError("URL hostname could not be resolved") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("URL hostname must resolve only to public IP addresses")
    return url


def validate_file_size(size_bytes: int, max_bytes: int) -> int:
    """Validate a non-negative file size against a configured upper bound."""
    if size_bytes < 0 or max_bytes <= 0:
        raise ValueError("file size and maximum must be non-negative and positive")
    if size_bytes > max_bytes:
        raise ValueError(f"file exceeds the {max_bytes}-byte size limit")
    return size_bytes
