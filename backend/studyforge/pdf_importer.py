from __future__ import annotations

from pathlib import Path
import fitz

from .hashing import cheap_file_fingerprint, file_sha1, slugify, stable_id
from .models import Asset, SourceDocument, StudyCard
from .sources import infer_subject_from_pdf
from .text_segmenter import segment_text


def render_page(page: fitz.Page, target: Path, zoom: float = 1.35) -> tuple[int, int]:
    target.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    pix.save(target)
    return pix.width, pix.height


def normalized_line_text(value: str) -> str:
    return " ".join(value.split()).strip()


def extract_line_rects(page: fitz.Page) -> list[tuple[str, fitz.Rect]]:
    line_rects: list[tuple[str, fitz.Rect]] = []
    page_dict = page.get_text("dict")
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text = normalized_line_text("".join(span.get("text", "") for span in line.get("spans", [])))
            if not text:
                continue
            line_rects.append((text, fitz.Rect(line["bbox"])))
    return line_rects


def segment_clip_rect(
    page: fitz.Page,
    line_rects: list[tuple[str, fitz.Rect]],
    line_start: int,
    line_end: int,
) -> fitz.Rect | None:
    if not line_rects or line_start < 0 or line_start >= len(line_rects):
        return None

    usable_end = min(max(line_end, line_start + 1), len(line_rects))
    selected = [rect for _, rect in line_rects[line_start:usable_end]]
    if not selected:
        return None

    page_rect = page.rect
    top = max(page_rect.y0, selected[0].y0 - 14)
    bottom = min(page_rect.y1, selected[-1].y1 + 18)
    if usable_end < len(line_rects):
        next_top = line_rects[usable_end][1].y0
        bottom = min(page_rect.y1, max(bottom, top + 32, next_top - 12))
    if bottom - top < 36:
        bottom = min(page_rect.y1, top + 48)

    return fitz.Rect(page_rect.x0, top, page_rect.x1, bottom)


def render_crop(page: fitz.Page, rect: fitz.Rect, target: Path, zoom: float = 1.8) -> tuple[int, int]:
    target.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect, alpha=False)
    pix.save(target)
    return pix.width, pix.height


def import_pdf(
    pdf_path: Path,
    asset_root: Path,
    *,
    subject: str | None = None,
    deck: str | None = None,
    max_pages: int | None = None,
    render_pages: bool = True,
) -> tuple[SourceDocument, list[StudyCard], list[str]]:
    pdf_path = pdf_path.resolve()
    subject = subject or infer_subject_from_pdf(pdf_path)
    deck = deck or pdf_path.stem
    warnings: list[str] = []

    doc = fitz.open(pdf_path)
    fingerprint = file_sha1(pdf_path) if pdf_path.stat().st_size < 35_000_000 else cheap_file_fingerprint(pdf_path)
    source_id = stable_id("pdf", pdf_path, length=18)
    source = SourceDocument(
        id=source_id,
        type="pdf",
        subject=subject,
        deck=deck,
        path=str(pdf_path),
        fingerprint=fingerprint,
        page_count=doc.page_count,
    )

    cards: list[StudyCard] = []
    page_limit = min(doc.page_count, max_pages) if max_pages is not None else doc.page_count
    source_slug = slugify(f"{subject}-{deck}")

    seen_card_ids: dict[str, int] = {}
    for page_index in range(page_limit):
        page = doc[page_index]
        page_number = page_index + 1
        text = page.get_text("text")
        segments = segment_text(text)
        line_rects = extract_line_rects(page)
        if not segments:
            segments = []
            warnings.append(f"{pdf_path.name} page {page_number}: no extractable text")

        page_asset: Asset | None = None
        if render_pages:
            page_rel = Path("pdf") / source_slug / f"page-{page_number:04d}.png"
            page_target = asset_root / page_rel
            width, height = render_page(page, page_target)
            page_asset = Asset(
                id=stable_id(source_id, "page", page_number),
                role="source_page",
                path=page_rel.as_posix(),
                source_path=str(pdf_path),
                width=width,
                height=height,
                sha1=cheap_file_fingerprint(page_target),
            )

        if not segments:
            card_id = stable_id(source_id, page_number, "empty")
            cards.append(
                StudyCard(
                    id=card_id,
                    subject=subject,
                    deck=deck,
                    source="page_fallback",
                    source_document_id=source_id,
                    source_path=str(pdf_path),
                    source_page=page_number,
                    source_item=None,
                    front_text=f"{deck} page {page_number}",
                    back_text="",
                    raw_text="",
                    confidence=0.12,
                    review_flags=["no_extractable_text", "needs_manual_review"],
                    assets=[page_asset] if page_asset else [],
                    tags=["pdf", "fallback"],
                )
            )
            continue

        for segment_index, segment in enumerate(segments, start=1):
            flags = list(segment.flags)
            assets = [page_asset] if page_asset else []
            front_line_end = (
                segment.answer_line_start
                if segment.answer_line_start is not None and segment.answer_line_start > segment.line_start
                else min(segment.line_start + 1, segment.line_end)
            )
            front_rect = segment_clip_rect(page, line_rects, segment.line_start, front_line_end)
            if front_rect is not None:
                front_rel = (
                    Path("pdf")
                    / source_slug
                    / "front"
                    / f"page-{page_number:04d}-item-{segment_index:03d}.png"
                )
                front_target = asset_root / front_rel
                front_width, front_height = render_crop(page, front_rect, front_target)
                assets.insert(
                    0,
                    Asset(
                        id=stable_id(source_id, "front", page_number, segment_index),
                        role="front_image",
                        path=front_rel.as_posix(),
                        source_path=str(pdf_path),
                        width=front_width,
                        height=front_height,
                        sha1=cheap_file_fingerprint(front_target),
                    ),
                )
                flags.append("has_front_crop")
            clip_rect = segment_clip_rect(page, line_rects, segment.line_start, segment.line_end)
            if clip_rect is not None:
                crop_rel = (
                    Path("pdf")
                    / source_slug
                    / "crops"
                    / f"page-{page_number:04d}-item-{segment_index:03d}.png"
                )
                crop_target = asset_root / crop_rel
                crop_width, crop_height = render_crop(page, clip_rect, crop_target)
                assets.append(
                    Asset(
                        id=stable_id(source_id, "crop", page_number, segment_index),
                        role="page_crop",
                        path=crop_rel.as_posix(),
                        source_path=str(pdf_path),
                        width=crop_width,
                        height=crop_height,
                        sha1=cheap_file_fingerprint(crop_target),
                    ),
                )
                flags.append("has_question_crop")
            if page_asset:
                flags.append("has_page_snapshot")
            if segment.confidence < 0.55:
                flags.append("needs_manual_review")
            base_card_id = stable_id(source_id, page_number, segment.raw_text)
            duplicate_index = seen_card_ids.get(base_card_id, 0)
            seen_card_ids[base_card_id] = duplicate_index + 1
            card_id = base_card_id if duplicate_index == 0 else stable_id(base_card_id, duplicate_index)
            cards.append(
                StudyCard(
                    id=card_id,
                    subject=subject,
                    deck=deck,
                    source="pdf" if "page_fallback" not in flags else "page_fallback",
                    source_document_id=source_id,
                    source_path=str(pdf_path),
                    source_page=page_number,
                    source_item=str(segment_index),
                    front_text=segment.front_text,
                    back_text=segment.back_text,
                    raw_text=segment.raw_text,
                    confidence=segment.confidence,
                    review_flags=flags,
                    assets=assets,
                    tags=["pdf", subject],
                )
            )

    return source, cards, warnings
