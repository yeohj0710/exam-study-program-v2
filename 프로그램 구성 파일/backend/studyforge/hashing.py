from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path


def stable_id(*parts: object, length: int = 16) -> str:
    payload = "\x1f".join(str(part) for part in parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:length]


def file_sha1(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def cheap_file_fingerprint(path: Path) -> str:
    stat = path.stat()
    return stable_id(path.resolve(), stat.st_size, int(stat.st_mtime_ns), length=20)


def slugify(value: str, fallback_prefix: str = "item") -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"[^\w가-힣]+", "-", normalized, flags=re.UNICODE)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-_")
    if normalized:
        return normalized[:90]
    return f"{fallback_prefix}-{stable_id(value, length=8)}"
