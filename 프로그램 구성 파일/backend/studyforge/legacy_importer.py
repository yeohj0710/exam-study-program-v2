from __future__ import annotations

from pathlib import Path
import shutil
from PIL import Image

from .hashing import cheap_file_fingerprint, file_sha1, slugify, stable_id
from .models import Asset, SourceDocument, StudyCard


def numeric_sort_key(path: Path) -> tuple[int, str]:
    return (int(path.stem), path.name) if path.stem.isdigit() else (999999, path.name)


def image_dimensions(path: Path) -> tuple[int | None, int | None]:
    try:
        with Image.open(path) as image:
            return image.width, image.height
    except Exception:
        return None, None


def import_legacy_bank(
    legacy_root: Path,
    asset_root: Path,
    *,
    copy_assets: bool = False,
    measure_images: bool = False,
) -> tuple[list[SourceDocument], list[StudyCard], list[str]]:
    legacy_root = legacy_root.resolve()
    if not legacy_root.exists():
        raise FileNotFoundError(legacy_root)

    sources: list[SourceDocument] = []
    cards: list[StudyCard] = []
    warnings: list[str] = []

    for deck_dir in sorted([path for path in legacy_root.iterdir() if path.is_dir()], key=lambda p: p.name):
        subject = deck_dir.name.replace(" 중간고사 오답노트", "").replace(" 중간고사", "")
        deck = deck_dir.name
        source_id = stable_id("legacy", deck_dir, length=18)
        source = SourceDocument(
            id=source_id,
            type="legacy_bank",
            subject=subject,
            deck=deck,
            path=str(deck_dir),
            fingerprint=cheap_file_fingerprint(deck_dir),
            page_count=None,
            imported_at=0.0,
        )
        sources.append(source)

        question_dirs = sorted(
            [path for path in deck_dir.iterdir() if path.is_dir()],
            key=lambda p: int(p.name) if p.name.isdigit() else 999999,
        )
        for question_dir in question_dirs:
            images = sorted(question_dir.glob("*.png"), key=numeric_sort_key)
            if not images:
                warnings.append(f"{question_dir}: no PNG files")
                continue

            card_id = stable_id(source_id, question_dir.name)
            deck_slug = slugify(deck)
            card_assets: list[Asset] = []

            for index, image in enumerate(images):
                if index == 0:
                    role = "front_image"
                elif index == len(images) - 1:
                    role = "answer_image"
                else:
                    role = "choice_image"

                if copy_assets:
                    rel = Path("legacy") / deck_slug / card_id / image.name
                    target = asset_root / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(image, target)
                    stored_path = rel.as_posix()
                    stored_hash = file_sha1(target) if measure_images else cheap_file_fingerprint(target)
                else:
                    stored_path = str(image)
                    stored_hash = cheap_file_fingerprint(image)

                width, height = image_dimensions(image) if measure_images else (None, None)
                card_assets.append(
                    Asset(
                        id=stable_id(card_id, image.name),
                        role=role,
                        path=stored_path,
                        source_path=str(image),
                        width=width,
                        height=height,
                        sha1=stored_hash,
                    )
                )

            flags: list[str] = []
            if len(images) < 2:
                flags.append("missing_answer_image")
            cards.append(
                StudyCard(
                    id=card_id,
                    subject=subject,
                    deck=deck,
                    source="legacy_capture",
                    source_document_id=source_id,
                    source_path=str(question_dir),
                    source_page=None,
                    source_item=question_dir.name,
                    front_text=f"{deck} #{question_dir.name}",
                    back_text="",
                    raw_text="",
                    confidence=1.0 if len(images) >= 2 else 0.45,
                    review_flags=flags,
                    assets=card_assets,
                    tags=["legacy", subject],
                    created_at=0.0,
                    updated_at=0.0,
                )
            )

    return sources, cards, warnings
