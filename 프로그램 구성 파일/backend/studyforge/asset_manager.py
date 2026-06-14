from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path

IMAGE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@dataclass
class SavedAsset:
    relative_path: str
    markdown: str
    path: str
    sha1: str


def _safe_folder_name(value: str) -> str:
    safe = "".join("-" if char in '<>:"/\\|?*' or ord(char) < 32 else char for char in value).strip(" .")
    return safe or "studyset"


def save_image_asset(
    asset_root: Path,
    *,
    studyset_slug: str,
    content: bytes,
    content_type: str,
    alt_text: str = "image",
) -> SavedAsset:
    extension = IMAGE_EXTENSIONS.get(content_type.lower())
    if extension is None:
        raise ValueError(f"Unsupported image content type: {content_type}")

    digest = sha1(content).hexdigest()
    stored_slug = _safe_folder_name(studyset_slug)
    filename = f"img-{digest[:12]}{extension}"
    target = (asset_root / stored_slug / filename).resolve()
    root = asset_root.resolve()
    if not target.is_relative_to(root):
        raise ValueError("Invalid asset path.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    relative_path = f"assets/{stored_slug}/{filename}"
    return SavedAsset(
        relative_path=relative_path,
        markdown=f"![{alt_text}]({relative_path})",
        path=str(target),
        sha1=digest,
    )
